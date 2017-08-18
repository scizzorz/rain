from . import ast as A
from . import error as Q
from . import module as M
from . import token as K

end = K.end_token()
indent = K.indent_token()
dedent = K.dedent_token()
newline = K.newline_token()

binary_ops = {
  '::': 100,

  '*': 90,
  '/': 90,
  '+': 80,
  '-': 80,

  '$': 70,

  '<': 60,
  '>': 60,
  '<=': 60,
  '>=': 60,
  '==': 60,
  '!=': 60,

  '&': 30,
  '|': 30,
}

rassoc = {
  '::',
}


class context:
  def __init__(self, stream, *, file=None):
    self.file = file
    self.qname, self.mname = M.find_name(file)
    self._mod = None
    self._eng = None
    self._builtin = None
    self._so = None

    self.token = None
    self.stream = stream
    self.peek = next(stream)
    self.next()
    self.past = []

    self.macros = {}

  def next(self):
    if self.token:
      self.past.append(self.token.pos(file=self.file))

    self.token = self.peek
    try:
      self.peek = next(self.stream)
    except StopIteration:
      self.peek = K.end_token()

  def expect(self, *tokens):
    return self.token in tokens

  def consume(self, *tokens):
    if self.expect(*tokens):
      token = self.token
      self.next()
      return token

  def require(self, *tokens):
    if self.expect(*tokens):
      token = self.token
      self.next()
      return token

    if len(tokens) > 1:
      choices = ', '.join(str(x) for x in tokens)
      msg = 'Unexpected {!s}; expected one of {}'.format(self.token, choices)
    else:
      msg = 'Unexpected {!s}; expected {!s}'.format(self.token, tokens[0])

    Q.abort(msg, pos=self.token.pos(file=self.file))


# program :: (stmt NEWLINE)+ EOF
def program(ctx):
  stmts = []
  while not ctx.expect(end):
    stmts.append(stmt(ctx))
    ctx.require(newline)

  ctx.require(end)

  return A.program_node(stmts)


# block :: INDENT (stmt NEWLINE)+ DEDENT
def block(ctx):
  stmts = []
  ctx.require(indent)

  while not ctx.expect(dedent):
    stmts.append(stmt(ctx))
    ctx.require(newline)

  ctx.require(dedent)

  return A.block_node(stmts)


# stmt :: 'bind' NAME (',' NAME)*
#       | 'break' ('if' binexpr)?
#       | 'continue' ('if' binexpr)?
#       | 'for' var_prefix 'in' binexpr block
#       | if_stmt
#       | 'loop' block
#       | 'pass'
#       | 'return' compound?
#       | 'save' (NAME '=')? compound
#       | 'var' var_prefix ('=' compound)?
#       | 'while' binexpr block
#       | assn_prefix ('=' compound | fnargs | ':' NAME  fnargs)
def stmt(ctx):
  if ctx.consume(K.keyword_token('bind')):
    names = fnparams(ctx, parens=False)
    return A.bind_node(names)

  if ctx.consume(K.keyword_token('break')):
    if ctx.consume(K.keyword_token('if')):
      return A.break_node(binexpr(ctx))

    return A.break_node()

  if ctx.consume(K.keyword_token('continue')):
    if ctx.consume(K.keyword_token('if')):
      return A.cont_node(binexpr(ctx))

    return A.cont_node()

  if ctx.consume(K.keyword_token('for')):
    name = var_prefix(ctx)
    ctx.require(K.keyword_token('in'))
    func = binexpr(ctx)
    body = block(ctx)

    return A.for_node(name, func, body)

  if ctx.expect(K.keyword_token('if')):
    return if_stmt(ctx)

  if ctx.consume(K.keyword_token('loop')):
    body = block(ctx)
    return A.loop_node(body)

  if ctx.consume(K.keyword_token('pass')):
    return A.pass_node()

  if ctx.consume(K.keyword_token('return')):
    if ctx.expect(newline):
      return A.return_node()

    return A.return_node(compound(ctx))

  if ctx.consume(K.keyword_token('save')):
    val = compound(ctx)
    if isinstance(val, A.name_node) and ctx.consume(K.symbol_token('=')):
      rhs = compound(ctx)
      return A.save_node(rhs, name=val.value)

    return A.save_node(val)

  if ctx.consume(K.keyword_token('var')):
    lhs = var_prefix(ctx)
    rhs = None
    if ctx.consume(K.symbol_token('=')):
      rhs = compound(ctx)
    return A.assn_node(lhs, rhs, var=True)

  if ctx.consume(K.keyword_token('while')):
    pred = binexpr(ctx)
    body = block(ctx)
    return A.while_node(pred, body)

  lhs = assn_prefix(ctx)

  if isinstance(lhs, (A.name_node, A.idx_node, list)):
    if ctx.consume(K.symbol_token('=')):
      rhs = compound(ctx)
      return A.assn_node(lhs, rhs, var=False)

  if ctx.expect(K.symbol_token('(')):
    pos = ctx.token.pos(file=ctx.file)
    args = fnargs(ctx)
    node = A.call_node(lhs, args, pop=True)
    node.coords = pos
    return node

  if ctx.consume(K.symbol_token(':')):
    name = ctx.require(K.name_token).value
    pos = ctx.past[-1]
    rhs = A.str_node(name)
    args = fnargs(ctx)
    node = A.meth_node(lhs, rhs, args, pop=True)
    node.coords = pos
    return node

  ctx.require(K.symbol_token('('), K.symbol_token(':'))


# if_stmt :: 'if' binexpr block (NEWLINE 'else' (if_stmt | block))?
def if_stmt(ctx):
  ctx.require(K.keyword_token('if'))
  pred = binexpr(ctx)
  body = block(ctx)
  els = None

  if ctx.peek == K.keyword_token('else'):
    ctx.require(newline)
    ctx.require(K.keyword_token('else'))
    if ctx.expect(K.keyword_token('if')):
      els = if_stmt(ctx)
    else:
      els = block(ctx)

  return A.if_node(pred, body, els)


# var_prefix :: '[' var_prefix (',' var_prefix)* ']'
#             | NAME
def var_prefix(ctx):
  if ctx.consume(K.symbol_token('[')):
    lst = []
    lst.append(var_prefix(ctx))
    while not ctx.consume(K.symbol_token(']')):
      ctx.require(K.symbol_token(','))
      lst.append(var_prefix(ctx))

    return lst

  node = A.name_node(ctx.require(K.name_token).value)
  node.coords = ctx.past[-1]
  return node


# assn_prefix :: '[' assn_prefix (',' assn_prefix)* ']'
#              | prefix ('.' NAME | '[' binexpr ']')*
def assn_prefix(ctx):
  if ctx.consume(K.symbol_token('[')):
    lst = []
    lst.append(assn_prefix(ctx))
    while not ctx.consume(K.symbol_token(']')):
      ctx.require(K.symbol_token(','))
      lst.append(assn_prefix(ctx))

    return lst

  lhs = prefix(ctx)
  rhs = None

  while True:
    if ctx.consume(K.symbol_token('.')):
      name = ctx.require(K.name_token).value
      rhs = A.str_node(name)
      lhs = A.idx_node(lhs, rhs)
      continue

    if ctx.consume(K.symbol_token('[')):
      rhs = binexpr(ctx)
      ctx.require(K.symbol_token(']'))
      lhs = A.idx_node(lhs, rhs)
      continue

    break

  return lhs


# array_expr :: '[' (binexpr (',' binexpr)*)? ','? ']'
def array_expr(ctx):
  ctx.require(K.symbol_token('['))
  arr = []
  if not ctx.expect(K.symbol_token(']')):
    arr.append(binexpr(ctx))
    while not ctx.expect(K.symbol_token(']')):
      ctx.require(K.symbol_token(','))
      if ctx.expect(K.symbol_token(']')):
        break
      arr.append(binexpr(ctx))

  ctx.require(K.symbol_token(']'))
  return arr


# dict_item :: ((NAME | '[' binexpr ']') '=' binexpr)
def dict_item(ctx):
  key = ctx.consume(K.name_token)

  if key:
    key = A.str_node(key.value)
  else:
    ctx.require(K.symbol_token('['))
    key = binexpr(ctx)
    ctx.require(K.symbol_token(']'))

  ctx.require(K.symbol_token('='))
  val = binexpr(ctx)

  return key, val


# dict_expr :: '{' (dict_item (',' dict_item)*)? ','? '}'
def dict_expr(ctx):
  ctx.require(K.symbol_token('{'))
  items = []
  if not ctx.expect(K.symbol_token('}')):
    items.append(dict_item(ctx))
    while not ctx.expect(K.symbol_token('}')):
      ctx.require(K.symbol_token(','))
      if ctx.expect(K.symbol_token('}')):
        break
      items.append(dict_item(ctx))

  ctx.require(K.symbol_token('}'))

  return items


# fnargs :: '(' (binexpr (',' binexpr)*)? ')'
def fnargs(ctx):
  ctx.require(K.symbol_token('('))
  args = []
  if not ctx.expect(K.symbol_token(')')):
    args.append(binexpr(ctx))
    while not ctx.expect(K.symbol_token(')')):
      ctx.require(K.symbol_token(','))
      args.append(binexpr(ctx))

  ctx.require(K.symbol_token(')'))
  return args


# fnparams :: '(' (NAME (',' NAME)*)? ')'
def fnparams(ctx, parens=True, tokens=[K.name_token]):
  if parens:
    ctx.require(K.symbol_token('('))

  params = []
  if ctx.expect(*tokens):
    params.append(ctx.require(*tokens).value)
    while ctx.consume(K.symbol_token(',')):
      params.append(ctx.require(*tokens).value)

  if parens:
    ctx.require(K.symbol_token(')'))

  return params


# compound :: 'func' fnparams ('->' binexpr | block)
#           | 'catch' block
#           | binexpr
def compound(ctx):
  if ctx.consume(K.keyword_token('func')):
    pos = ctx.past[-1]

    params = fnparams(ctx)

    if ctx.consume(K.operator_token('->')):
      exp = binexpr(ctx)

      node = A.func_node(params, A.return_node(exp))
      node.coords = pos
      return node

    body = block(ctx)

    node = A.func_node(params, body)
    node.coords = pos
    return node

  if ctx.consume(K.keyword_token('catch')):
    body = block(ctx)
    return A.catch_node(body)

  return binexpr(ctx)


# binexpr :: unexpr (OPERATOR unexpr)*
def binexpr(ctx):
  lhs = unexpr(ctx)
  pairs = []

  while ctx.expect(K.operator_token):
    op = ctx.require(K.operator_token)
    op.pos = op.pos(file=ctx.file)
    pairs.append((op, unexpr(ctx)))

  if pairs:
    lhs = bin_merge(lhs, pairs)

  return lhs


def bin_merge(lhs, pairs):
  op, rhs = pairs[0]
  pairs = pairs[1:]
  for nop, next in pairs:
    if binary_ops[nop.value] > binary_ops[op.value]:
      rhs = bin_merge(rhs, pairs)
      break
    elif nop.value in rassoc and binary_ops[nop.value] == binary_ops[op.value]:
      rhs = bin_merge(rhs, pairs)
      break
    else:
      lhs = A.binary_node(lhs, rhs, op.value)
      lhs.coords = op.pos
      op = nop
      rhs = next
      pairs = pairs[1:]

  node = A.binary_node(lhs, rhs, op.value)
  node.coords = op.pos
  return node


# unexpr :: ('-' | '!' | '$') unexpr
#         | simple
def unexpr(ctx):
  ops = ('-', '!', '$')
  if ctx.expect(*(K.operator_token(op) for op in ops)):
    op = ctx.require(K.operator_token).value
    pos = ctx.past[-1]
    node = A.unary_node(op, unexpr(ctx))
    node.coords = pos
    return node

  return simple(ctx)


# simple :: 'func' fnparams '->' binexpr
#         | array_expr
#         | dict_expr
#         | primary
def simple(ctx):
  if ctx.consume(K.keyword_token('func')):
    pos = ctx.past[-1]
    params = fnparams(ctx)
    ctx.require(K.operator_token('->'))
    exp = binexpr(ctx)

    node = A.func_node(params, A.return_node(exp))
    node.coords = pos
    return node

  if ctx.consume(K.keyword_token('foreign')):
    name = ctx.require(K.name_token, K.string_token).value
    params = fnparams(ctx)
    return A.foreign_node(name, params)

  if ctx.expect(K.symbol_token('[')):
    return A.array_node(array_expr(ctx))

  if ctx.expect(K.symbol_token('{')):
    return A.dict_node(dict_expr(ctx))

  return primary(ctx)


# primary :: prefix ('?'? fnargs | ':' NAME '?'? fnargs | '.' NAME | '[' binexpr ']')*
def primary(ctx):
  node = prefix(ctx)

  while True:
    if ctx.consume(K.symbol_token('?')):
      pos = ctx.token.pos(file=ctx.file)
      args = fnargs(ctx)
      node = A.call_node(node, args, catch=True)
      node.coords = pos
      continue

    if ctx.expect(K.symbol_token('(')):
      pos = ctx.token.pos(file=ctx.file)
      args = fnargs(ctx)
      node = A.call_node(node, args)
      node.coords = pos
      continue

    if ctx.consume(K.symbol_token(':')):
      name = ctx.require(K.name_token).value
      pos = ctx.past[-1]
      rhs = A.str_node(name)

      catch = bool(ctx.consume(K.symbol_token('?')))

      args = fnargs(ctx)
      node = A.meth_node(node, rhs, args, catch=catch)
      node.coords = pos

      continue

    if ctx.consume(K.symbol_token('.')):
      name = ctx.require(K.name_token).value
      rhs = A.str_node(name)
      node = A.idx_node(node, rhs)
      continue

    if ctx.consume(K.symbol_token('[')):
      rhs = binexpr(ctx)
      ctx.require(K.symbol_token(']'))
      node = A.idx_node(node, rhs)
      continue

    break

  return node


# prefix :: '(' binexpr ')'
#         | NAME | INT | FLOAT | BOOL | STRING | NULL | (TABLE dict_expr?)
def prefix(ctx):
  if ctx.consume(K.symbol_token('(')):
    node = binexpr(ctx)
    ctx.require(K.symbol_token(')'))
    return node

  if ctx.expect(K.int_token):
    node = A.int_node(ctx.require(K.int_token).value)

  elif ctx.expect(K.float_token):
    node = A.float_node(ctx.require(K.float_token).value)

  elif ctx.expect(K.bool_token):
    node = A.bool_node(ctx.require(K.bool_token).value)

  elif ctx.expect(K.string_token):
    node = A.str_node(ctx.require(K.string_token).value)

  elif ctx.consume(K.null_token):
    node = A.null_node()

  elif ctx.consume(K.table_token):
    node = A.table_node()

    if ctx.expect(K.symbol_token('{')):
      pos = ctx.past[-1]
      node = A.dict_node(dict_expr(ctx), set_meta=False)
      node.coords = pos
      return node

  else:
    node = A.name_node(ctx.require(K.name_token).value)

  node.coords = ctx.past[-1]
  return node
