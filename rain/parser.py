from . import ast as A
from . import compiler as C
from . import engine as E
from . import error as Q
from . import module as M
from . import token as K
from . import types as T
from ctypes import byref
from os import environ as ENV
from os.path import join
import os.path

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

class macro:
  def __init__(self, name, node, parses):
    self.name = name
    self.parses = parses
    mod = M.Module(name=name, mmap=True)

    # compile builtins
    builtin = C.get_compiler(join(ENV['RAINLIB'], '_pkg.rn'))
    builtin.goodies()

    # compile lib.ast and use its links/libs
    ast = C.get_compiler(join(ENV['RAINLIB'], 'ast.rn'), mmap=True)
    ast.goodies()
    so = ast.compile_links()

    # import builtins
    for name, val in builtin.mod.globals.items():
      mod[name] = val
    mod.import_from(builtin.mod)

    # emit the macro code
    A.import_node('ast').emit(mod)  # auto-import lib/ast.rn

    # define gensym
    symcount = A.name_node(':symcount')
    gensym = A.name_node('gensym')
    tostr = A.name_node('tostr')

    A.assn_node(symcount, A.int_node(0), let=True).emit(mod)
    A.assn_node(gensym, A.func_node([], A.block_node([
      A.save_node(A.binary_node(A.str_node(':{}:'.format(self.name)),
                                A.call_node(tostr, [symcount]), '$')),
      A.assn_node(symcount, A.binary_node(symcount, A.int_node(1), '+'))
    ])), let=True).emit(mod)

    node.expand(mod)

    # create the execution engine and link everthing
    self.eng = E.Engine(llvm_ir=mod.ir)
    self.eng.link_file(ast.ll, *ast.links)
    self.eng.add_lib(so)
    self.eng.finalize()

  def parse(self, ctx):
    return [fn(ctx) for fn in self.parses]

  def expand(self, ctx):
    args = self.parse(ctx)

    arg_boxes = [self.eng.to_rain(arg) for arg in args]

    ret_box = T.cbox(0, 0, 0)
    func = self.eng.get_func('macro.func.main', T.carg, *[T.carg] * len(self.parses))
    func(byref(ret_box), *[byref(arg) for arg in arg_boxes])
    new_node = self.eng.to_py(ret_box)

    return new_node


class context:
  def __init__(self, stream, *, file=None):
    self.file = file
    self.qname, self.mname = M.find_name(file)

    self.stream = stream
    self.peek = next(stream)
    self.next()

    self.macros = {}

  def next(self):
    self.token = self.peek
    try:
      self.peek = next(self.stream)
    except StopIteration:
      self.peek = K.end_token()

  def register_macro(self, name, node, parses):
    self.macros[name] = macro(self.qname + ':' + name, node, parses)

  def expand_macro(self, name):
    return self.macros[name].expand(self)

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

# expr_block :: INDENT (expr NEWLINE)+ DEDENT
def expr_block(ctx):
  exprs = []
  ctx.require(indent)

  while not ctx.expect(dedent):
    exprs.append(expr(ctx))
    ctx.require(newline)

  ctx.require(dedent)

  return A.block_node(exprs)


# stmt :: 'let' NAME '=' expr
#       | 'export' NAME '=' expr
#       | 'export' NAME 'as' 'foreign' (NAME | STRING)
#       | 'import' (NAME | STRING) ('as' NAME)?
#       | 'macro' NAME fnparams 'as' fnparams block
#       | macro_exp
#       | 'link' STRING
#       | 'library' STRING
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
    name = ctx.require(K.name_token, K.string_token)
    base, fname = os.path.split(ctx.file)
    file = M.find_rain(name.value, paths=[base])

    if not file:
      Q.abort("Can't find module {!r}", name.value, pos=name.pos(file=ctx.file))

    name = name.value
    rename = None
    if ctx.consume(K.keyword_token('as')):
      rename = ctx.require(K.name_token).value

    comp = C.get_compiler(file)
    comp.read()
    comp.lex()
    comp.parse()

    prefix = rename or comp.mname
    for key, val in comp.parser.macros.items():
      ctx.macros[prefix + '.' + key] = val

    return A.import_node(name, rename)

  if ctx.consume(K.keyword_token('macro')):
    type_options = {
      'expr': expr,
      'args': fnargs,
      'params': fnparams,
      'block': block,
      'exprblock': expr_block,
      'stmt': stmt,
      'name': lambda x: x.require(K.name_token).value,
      'namestr': lambda x: x.require(K.name_token, K.string_token).value,
      'string': lambda x: x.require(K.string_token).value,
      'int': lambda x: x.require(K.int_token).value,
      'float': lambda x: x.require(K.float_token).value,
      'bool': lambda x: x.require(K.bool_token).value,
    }

    name = ctx.require(K.name_token)
    if name.value in ctx.macros:
      Q.abort('Redefinition of macro {!r}', name.value, pos=name.pos(file=ctx.file))

    name = name.value
    types = fnparams(ctx, tokens=[K.name_token(n) for n in type_options])
    ctx.require(K.keyword_token('as'))
    params = fnparams(ctx)
    body = block(ctx)

    node = A.macro_node(name, types, params, body)
    ctx.register_macro(name, node, [type_options[x] for x in types])
    return node

  if ctx.expect(K.symbol_token('@')):
    return macro_exp(ctx)

  if ctx.consume(K.keyword_token('link')):
    name = ctx.require(K.string_token).value
    return A.link_node(name)

  if ctx.consume(K.keyword_token('library')):
    name = ctx.require(K.string_token).value
    return A.lib_node(name)

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


# macro_exp :: '@' NAME ('.' NAME)* ***
def macro_exp(ctx):
  ctx.require(K.symbol_token('@'))
  name = ctx.require(K.name_token)
  pos = name.pos(file=ctx.file)
  name = name.value

  while ctx.consume(K.symbol_token('.')):
    name += '.' + ctx.require(K.name_token).value
    pos.len = len(name)

  if name not in ctx.macros:
    Q.abort('Unknown macro {!r}', name, pos=pos)

  res = ctx.expand_macro(name)
  return res


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



# expr :: macro_exp
#       | binexpr
def expr(ctx):
  if ctx.expect(K.symbol_token('@')):
    return macro_exp(ctx)

  return binexpr(ctx)


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
