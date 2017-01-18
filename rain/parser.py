from . import lexer as L
from . import token as K
from . import ast as A

end = K.end_token()
indent = K.indent_token()
dedent = K.dedent_token()
newline = K.newline_token()

binary_ops = {
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


class context:
  def __init__(self, stream, *, file=None):
    self.file = file
    self.stream = stream
    self.peek = next(stream)
    self.next()

  def next(self):
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

    self.panic('expected one of {}, found {!r}', ' | '.join(repr(x) for x in tokens), self.token, line=self.token.line, col=self.token.col)

  def panic(self, fmt, *args, line=None, col=None):
    prefix = ''
    if self.file:
      prefix += self.file + ':'
    if line and col:
      prefix += str(line) + ':' + str(col) + ':'

    msg = fmt.format(*args)

    if prefix:
      raise SyntaxError('{} {}'.format(prefix, msg))

    raise SyntaxError(msg)

def program(ctx):
  stmts = []
  while not ctx.expect(end):
    stmts.append(stmt(ctx))
    ctx.require(newline)

  ctx.require(end)

  return A.program_node(stmts)

def block(ctx):
  stmts = []
  ctx.require(indent)

  while not ctx.expect(dedent):
    stmts.append(stmt(ctx))
    ctx.require(newline)

  ctx.require(dedent)

  return A.block_node(stmts)

def if_stmt(ctx):
  ctx.require(K.keyword_token('if'))
  pred = expr(ctx)
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

def stmt(ctx):
  if ctx.consume(K.keyword_token('let')):
    lhs = A.name_node(ctx.require(K.name_token))
    ctx.require(K.symbol_token('='))
    rhs = expr(ctx)
    return A.assn_node(lhs, rhs, let=True)

  if ctx.expect(K.keyword_token('if')):
    return if_stmt(ctx)

  if ctx.consume(K.keyword_token('import')):
    name = ctx.require(K.name_token, K.string_token).value
    rename = None
    if ctx.consume(K.keyword_token('as')):
      rename = ctx.require(K.name_token).value

    return A.import_node(name, rename)

  if ctx.consume(K.keyword_token('for')):
    name = ctx.require(K.name_token)
    ctx.require(K.keyword_token('in'))
    func = expr(ctx)
    body = block(ctx)
    return A.for_node(name, func, body)

  if ctx.consume(K.keyword_token('with')):
    func = expr(ctx)
    ctx.require(K.keyword_token('as'))
    params = fnparams(ctx)
    body = block(ctx)
    return A.with_node(func, params, body)

  if ctx.consume(K.keyword_token('while')):
    pred = expr(ctx)
    body = block(ctx)
    return A.while_node(pred, body)

  if ctx.consume(K.keyword_token('until')):
    pred = expr(ctx)
    body = block(ctx)
    return A.until_node(pred, body)

  if ctx.consume(K.keyword_token('loop')):
    body = block(ctx)
    return A.loop_node(body)

  if ctx.consume(K.keyword_token('pass')):
    return A.pass_node()

  if ctx.consume(K.keyword_token('break')):
    if ctx.consume(K.keyword_token('if')):
      return A.break_node(expr(ctx))

    return A.break_node()

  if ctx.consume(K.keyword_token('continue')):
    if ctx.consume(K.keyword_token('if')):
      return A.cont_node(expr(ctx))

    return A.cont_node()

  if ctx.consume(K.keyword_token('return')):
    if ctx.expect(newline):
      return A.return_node()

    return A.return_node(expr(ctx))

  if ctx.consume(K.keyword_token('save')):
    return A.save_node(expr(ctx))

  lhs = assn_prefix(ctx)

  if ctx.consume(K.symbol_token('=')):
    rhs = expr(ctx)
    return A.assn_node(lhs, rhs, let=False)

  if ctx.expect(K.symbol_token('(')):
    args = fnargs(ctx)
    return A.call_node(lhs, args)

  if ctx.consume(K.symbol_token(':')):
    name = ctx.require(K.name_token)
    rhs = A.str_node(name.value)
    args = fnargs(ctx)
    return A.meth_node(lhs, rhs, args)

def assn_prefix(ctx):
  lhs = prefix(ctx)
  rhs = None

  while True:

    if ctx.consume(K.symbol_token('.')):
      name = ctx.require(K.name_token)
      rhs = A.str_node(name.value)
      lhs = A.idx_node(lhs, rhs)
      continue

    if ctx.consume(K.symbol_token('[')):
      rhs = expr(ctx)
      ctx.require(K.symbol_token(']'))
      lhs = A.idx_node(lhs, rhs)
      continue

    break

  return lhs

def fnargs(ctx):
  ctx.require(K.symbol_token('('))
  args = []
  if not ctx.expect(K.symbol_token(')')):
    args.append(expr(ctx))
    while not ctx.expect(K.symbol_token(')')):
      ctx.require(K.symbol_token(','))
      args.append(expr(ctx))

  ctx.require(K.symbol_token(')'))
  return args

def fnparams(ctx):
  ctx.require(K.symbol_token('('))
  params = []
  if ctx.expect(K.name_token):
    params.append(ctx.require(K.name_token))
    while not ctx.expect(K.symbol_token(')')):
      ctx.require(K.symbol_token(','))
      params.append(ctx.require(K.name_token))

  ctx.require(K.symbol_token(')'))

  return params

def expr(ctx):
  node = binexpr(ctx)
  if ctx.consume(K.keyword_token('is')):
    typ = ctx.require(K.type_token, K.null_token, K.table_token, K.keyword_token('func'))
    return A.is_node(node, typ)

  return node

def binexpr(ctx):
  lhs = unexpr(ctx)
  pairs = []

  while ctx.expect(K.operator_token):
    op = ctx.require(K.operator_token)
    pairs.append((op.value, unexpr(ctx)))

  if pairs:
    lhs = bin_merge(lhs, pairs)

  return lhs

def bin_merge(lhs, pairs):
  op, rhs = pairs[0]
  pairs = pairs[1:]
  for nop, next in pairs:
    if binary_ops[nop] > binary_ops[op]:
      rhs = bin_merge(rhs, pairs)
      break
    else:
      lhs = A.binary_node(lhs, rhs, op)
      op = nop
      rhs = next
      pairs = pairs[1:]

  return A.binary_node(lhs, rhs, op)

def unexpr(ctx):
  if ctx.expect(K.operator_token('-'), K.operator_token('!')):
    return A.unary_node(ctx.require(K.operator_token).value, simple(ctx))

  return simple(ctx)

def simple(ctx):
  # -> fndef
  if ctx.consume(K.keyword_token('func')):
    params = fnparams(ctx)

    # -> quick function
    if ctx.consume(K.operator_token('->')):
      exp = expr(ctx)
      return A.func_node(params, A.return_node(exp))

    body = block(ctx)
    return A.func_node(params, body)

  # -> extern
  if ctx.consume(K.keyword_token('extern')):
    name = ctx.require(K.name_token, K.string_token)
    return A.extern_node(name)

  # -> LITERAL
  if ctx.expect(K.int_token):
    return A.int_node(ctx.require(K.int_token).value)

  if ctx.expect(K.float_token):
    return A.float_node(ctx.require(K.float_token).value)

  if ctx.expect(K.bool_token):
    return A.bool_node(ctx.require(K.bool_token).value)

  if ctx.expect(K.string_token):
    return A.str_node(ctx.require(K.string_token).value)

  if ctx.consume(K.null_token):
    return A.null_node()

  if ctx.consume(K.table_token):
    metatable = None
    if ctx.consume(K.keyword_token('from')):
      metatable = expr(ctx)

    return A.table_node(metatable)

  return primary(ctx)

def primary(ctx):
  node = prefix(ctx)

  while True:
    if ctx.expect(K.symbol_token('(')):
      args = fnargs(ctx)
      node = A.call_node(node, args)
      continue

    if ctx.consume(K.symbol_token(':')):
      name = ctx.require(K.name_token)
      rhs = A.str_node(name.value)

      if ctx.expect(K.symbol_token('(')):
        args = fnargs(ctx)
        node = A.meth_node(node, rhs, args)
      else:
        node = A.bind_node(node, rhs)

      continue

    if ctx.consume(K.symbol_token('.')):
      name = ctx.require(K.name_token)
      rhs = A.str_node(name.value)
      node = A.idx_node(node, rhs)
      continue

    if ctx.consume(K.symbol_token('[')):
      rhs = expr(ctx)
      ctx.require(K.symbol_token(']'))
      node = A.idx_node(node, rhs)
      continue

    break

  return node

def prefix(ctx):
  if ctx.consume(K.symbol_token('(')):
    node = expr(ctx)
    ctx.require(K.symbol_token(')'))
    return node

  return A.name_node(ctx.require(K.name_token).value)
