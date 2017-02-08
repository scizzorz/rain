from . import token as K
from . import ast as A
from . import module as M
from . import engine as E

from ctypes import byref
import ctypes

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
    self.coord = (0, 0)
    self.next()

    self.macros = {}

  def next(self):
    self.token = self.peek
    try:
      self.peek = next(self.stream)
    except StopIteration:
      self.peek = K.end_token()

  def register_macro(self, name, node, parses):
    # TODO: panic on redef
    # TODO: better data structure?
    self.macros[name] = (node, parses)

  def expand_macro(self, name):
    mod = M.Module(name='macro')
    node = self.macros[name][0]
    parses = self.macros[name][1]

    node.expand(mod)

    # TODO: figure out how to automatically find all of this crap
    # TODO: import builtins?
    # TODO: import ast?
    eng = E.Engine(llvm_ir=mod.ir)
    eng.link_file('tmp/rain.ll', 'tmp/util.ll', 'tmp/lib.ll', 'tmp/lib.env.ll', 'tmp/lib.except.ll', 'tmp/except.ll', 'tmp/env.ll')
    eng.add_lib('/usr/lib/libgc.so', '/usr/lib/libgcc_s.so.1')
    eng.finalize()

    args = [fn(self) for fn in parses]
    arg_boxes = [eng.coerce(arg) for arg in args]

    new_node_box = E.Box(0, 0, 0)
    func = eng.get_func('macro.func.0', E.Arg, *[E.Arg] * len(parses))
    func(byref(new_node_box), *[byref(arg) for arg in arg_boxes])

    new_node_name_box = eng.rain_get_str(new_node_box, "tag")
    print("The macro returned:", new_node_name_box.as_str())

    return new_node_box

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
      msg = 'Unexpected {!s}; expected one of {}'.format(self.token, ' | '.join(str(x) for x in tokens))
    else:
      msg = 'Unexpected {!s}; expected {!s}'.format(self.token, tokens[0])

    self.panic(msg, line=self.token.line, col=self.token.col)

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


# stmt :: 'let' NAME '=' expr
#       | 'export' NAME '=' expr
#       | 'export' NAME 'as' 'foreign' (NAME | STRING)
#       | 'import' (NAME | STRING) ('as' NAME)?
#       | 'link' STRING
#       | if_stmt
#       | 'catch' NAME block
#       | 'for' NAME 'in' expr block
#       | 'with' expr ('as' NAME (',' NAME)*)
#       | 'while' expr block
#       | 'until' expr block
#       | 'loop' block
#       | 'pass'
#       | 'break' ('if' expr)?
#       | 'continue' ('if' expr)?
#       | 'return' expr?
#       | 'save' expr
#       | assn_prefix ('=' expr | fnargs | ':' NAME  fnargs)
def stmt(ctx):
  if ctx.consume(K.keyword_token('let')):
    lhs = A.name_node(ctx.require(K.name_token).value)
    ctx.require(K.symbol_token('='))
    rhs = expr(ctx)
    return A.assn_node(lhs, rhs, let=True)

  if ctx.consume(K.keyword_token('export')):
    name = ctx.require(K.name_token).value

    if ctx.consume(K.symbol_token('=')):
      rhs = expr(ctx)
      return A.assn_node(A.name_node(name), rhs, export=True)

    if ctx.consume(K.keyword_token('as')):
      ctx.require(K.keyword_token('foreign'))
      rename = ctx.require(K.string_token, K.name_token).value
      return A.export_foreign_node(name, rename)

  if ctx.consume(K.keyword_token('import')):
    name = ctx.require(K.name_token, K.string_token).value
    rename = None
    if ctx.consume(K.keyword_token('as')):
      rename = ctx.require(K.name_token).value

    print('macro import:', name)
    return A.import_node(name, rename)

  if ctx.consume(K.keyword_token('macro')):
    type_options = {
      'expr': expr,
      'block': block,
      'string': lambda x: x.require(K.string_token).value,
    }

    name = ctx.require(K.name_token).value
    types = fnparams(ctx, tokens=[K.name_token(n) for n in type_options])
    ctx.require(K.keyword_token('as'))
    params = fnparams(ctx)
    body = block(ctx)

    print('macro def:', name, params)
    node = A.macro_node(name, types, params, body)
    ctx.register_macro(name, node, [type_options[x] for x in types])
    return node

  if ctx.consume(K.symbol_token('@')):
    name = ctx.require(K.name_token).value
    print('macro exp:', name)
    res = ctx.expand_macro(name)
    return A.pass_node()

  if ctx.consume(K.keyword_token('link')):
    name = ctx.require(K.string_token).value
    return A.link_node(name)

  if ctx.expect(K.keyword_token('if')):
    return if_stmt(ctx)

  if ctx.consume(K.keyword_token('catch')):
    name = ctx.require(K.name_token).value
    body = block(ctx)
    return A.catch_node(name, body)

  if ctx.consume(K.keyword_token('for')):
    name = ctx.require(K.name_token).value
    ctx.require(K.keyword_token('in'))
    func = expr(ctx)
    body = block(ctx)
    return A.for_node(name, func, body)

  if ctx.consume(K.keyword_token('with')):
    func = expr(ctx)

    if ctx.consume(K.keyword_token('as')):
      params = fnparams(ctx, parens=False)
    else:
      params = []

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
    name = ctx.require(K.name_token).value
    rhs = A.str_node(name)
    args = fnargs(ctx)
    return A.meth_node(lhs, rhs, args)


# if_stmt :: 'if' expr block (NEWLINE 'else' (if_stmt | block))?
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


# assn_prefix :: prefix ('.' NAME | '[' expr ']')*
def assn_prefix(ctx):
  lhs = prefix(ctx)
  rhs = None

  while True:

    if ctx.consume(K.symbol_token('.')):
      name = ctx.require(K.name_token).value
      rhs = A.str_node(name)
      lhs = A.idx_node(lhs, rhs)
      continue

    if ctx.consume(K.symbol_token('[')):
      rhs = expr(ctx)
      ctx.require(K.symbol_token(']'))
      lhs = A.idx_node(lhs, rhs)
      continue

    break

  return lhs


# fnargs :: '(' (expr (',' expr)*)? ')'
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


# expr :: binexpr ('is' (TYPE | NULL | TABLE | 'func'))?
def expr(ctx):
  node = binexpr(ctx)
  if ctx.consume(K.keyword_token('is')):
    typ = ctx.require(K.type_token, K.null_token, K.table_token, K.keyword_token('func')).value
    return A.is_node(node, typ)

  return node


# binexpr :: unexpr (OPERATOR unexpr)*
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


# unexpr :: ('-' | '!') simple
#         | simple
def unexpr(ctx):
  if ctx.expect(K.operator_token('-'), K.operator_token('!')):
    return A.unary_node(ctx.require(K.operator_token).value, simple(ctx))

  return simple(ctx)


# simple :: 'func' fnparams ('->' expr | block)
#         | 'foreign' (NAME | STRING) fnparams
#         | INT | FLOAT | BOOL | STRING | NULL | TABLE ('from' expr)?
#         | primary
def simple(ctx):
  if ctx.consume(K.keyword_token('func')):
    params = fnparams(ctx)

    if ctx.consume(K.operator_token('->')):
      exp = expr(ctx)
      return A.func_node(params, A.return_node(exp))

    body = block(ctx)
    return A.func_node(params, body)

  if ctx.consume(K.keyword_token('foreign')):
    name = ctx.require(K.name_token, K.string_token).value
    params = fnparams(ctx)
    return A.foreign_node(name, params)

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


# primary :: prefix ('?'? fnargs | ':' NAME '?'? fnargs | '.' NAME | '[' expr ']')*
def primary(ctx):
  node = prefix(ctx)

  while True:
    if ctx.consume(K.symbol_token('?')):
      args = fnargs(ctx)
      node = A.call_node(node, args, catch=True)
      continue

    if ctx.expect(K.symbol_token('(')):
      args = fnargs(ctx)
      node = A.call_node(node, args)
      continue

    if ctx.consume(K.symbol_token(':')):
      name = ctx.require(K.name_token).value
      rhs = A.str_node(name)

      catch = bool(ctx.consume(K.symbol_token('?')))

      args = fnargs(ctx)
      node = A.meth_node(node, rhs, args, catch=catch)

      continue

    if ctx.consume(K.symbol_token('.')):
      name = ctx.require(K.name_token).value
      rhs = A.str_node(name)
      node = A.idx_node(node, rhs)
      continue

    if ctx.consume(K.symbol_token('[')):
      rhs = expr(ctx)
      ctx.require(K.symbol_token(']'))
      node = A.idx_node(node, rhs)
      continue

    break

  return node


# prefix :: '(' expr ')'
#         | NAME
def prefix(ctx):
  if ctx.consume(K.symbol_token('(')):
    node = expr(ctx)
    ctx.require(K.symbol_token(')'))
    return node

  return A.name_node(ctx.require(K.name_token).value)
