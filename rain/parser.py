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

class macro:
  def __init__(self, ctx, name, node, parses):
    self.name = name
    self.parses = parses
    self.ctx = ctx # save this as our "source" context

    mod = M.Module(self.name)
    mod.import_scope(ctx.builtin_mod.mod)
    mod.import_llvm(ctx.builtin_mod.mod)
    A.import_node('ast').emit(mod)

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

    node.expand(mod, self.name)

    ctx.eng.add_ir(mod.ir)
    ctx.eng.finalize()

  def parse(self, ctx):
    return [fn(ctx) for fn in self.parses]

  def expand(self, ctx):
    args = self.parse(ctx)

    arg_boxes = [self.ctx.eng.to_rain(arg) for arg in args]

    ret_box = T.cbox(0, 0, 0)
    func = self.ctx.eng.get_func('macro.func.main:' + self.name, T.carg, *[T.carg] * len(self.parses))
    func(byref(ret_box), *[byref(arg) for arg in arg_boxes])
    new_node = self.ctx.eng.to_py(ret_box)

    return new_node


class context:
  def __init__(self, stream, *, file=None):
    self.file = file
    self.qname, self.mname = M.find_name(file)
    self._mod = None
    self._eng = None
    self._builtin = None
    self._ast = None
    self._so = None

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

  @property
  def ast_mod(self):
    if self._ast is None:
      # compile lib.ast and use its links/libs
      self._ast = C.get_compiler(join(ENV['RAINLIB'], 'ast.rn'))
      self._ast.build()

    return self._ast

  @property
  def builtin_mod(self):
    if self._builtin is None:
      # compile builtins
      self._builtin = C.get_compiler(join(ENV['RAINLIB'], '_pkg.rn'))
      self._builtin.build()

    return self._builtin

  @property
  def libs(self):
    if self._so is None:
      self._so = self.ast_mod.compile_links()

    return self._so

  @property
  def mod(self):
    if not self._mod:
      self._mod = M.Module('macros')

      # compile lib.ast and use its links/libs
      self._ast = C.get_compiler(join(ENV['RAINLIB'], 'ast.rn'))
      self._ast.build()
      self._so = self._ast.compile_links()

      # emit the macro code
      A.import_node('ast').emit(self._mod)  # auto-import lib/ast.rn

      # define gensym
      symcount = A.name_node(':symcount')
      gs = A.name_node('gs')
      gensym = A.name_node('gensym')
      tostr = A.name_node('tostr')

      A.assn_node(gs, A.table_node(), let=True).emit(self._mod)
      A.assn_node(symcount, A.int_node(0), let=True).emit(self._mod)
      A.assn_node(gensym, A.func_node([], A.block_node([
        A.save_node(A.binary_node(A.str_node(':{}:'.format(self.qname)),
                                  A.call_node(tostr, [symcount]), '$')),
        A.assn_node(symcount, A.binary_node(symcount, A.int_node(1), '+'))
      ])), let=True).emit(self._mod)

    return self._mod

  @property
  def eng(self):
    if not self._eng:
      self._eng = E.Engine(llvm_ir='')
      self._eng.add_lib(self.libs)
      self._eng.link_file(self.ast_mod.ll, *self.ast_mod.links)
      self._eng.finalize()
      self._eng.init_gc()
      self._eng.disable_gc() # this is a problem when sharing code between macros
      self._eng.init_ast()

    return self._eng

  def register_macro(self, name, node, parses):
    self.macros[name] = macro(self, self.qname + ':' + name, node, parses)

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


# stmt :: 'let' let_prefix '=' compound
#       | 'export' NAME '=' compound
#       | 'export' NAME 'as' 'foreign' (NAME | STRING)
#       | 'import' (NAME | STRING) ('as' NAME)?
#       | 'macro' NAME fnparams 'as' fnparams block
#       | macro_exp
#       | 'link' STRING
#       | 'library' STRING
#       | if_stmt
#       | 'catch' NAME block
#       | 'for' NAME 'in' binexpr block
#       | 'with' binexpr ('as' NAME (',' NAME)*)
#       | 'while' binexpr block
#       | 'until' binexpr block
#       | 'loop' block
#       | 'pass'
#       | 'break' ('if' binexpr)?
#       | 'continue' ('if' binexpr)?
#       | 'return' compound?
#       | 'save' compound
#       | assn_prefix ('=' compound | fnargs | ':' NAME  fnargs)
def stmt(ctx):
  if ctx.consume(K.keyword_token('let')):
    lhs = let_prefix(ctx)
    ctx.require(K.symbol_token('='))
    rhs = compound(ctx)
    return A.assn_node(lhs, rhs, let=True)

  if ctx.consume(K.keyword_token('export')):
    name = ctx.require(K.name_token).value

    if ctx.consume(K.symbol_token('=')):
      rhs = compound(ctx)
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
      'compound': compound,
      'expr': binexpr,
      'args': fnargs,
      'params': fnparams,
      'block': block,
      'argblock': fnargblock,
      'stmt': stmt,
      'name': lambda x: x.require(K.name_token).value,
      'namestr': lambda x: x.require(K.name_token, K.string_token).value,
      'str': lambda x: x.require(K.string_token).value,
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
    name = let_prefix(ctx)
    ctx.require(K.keyword_token('in'))
    func = binexpr(ctx)
    body = block(ctx)

    return A.for_node(name, func, body)

  if ctx.consume(K.keyword_token('with')):
    func = binexpr(ctx)

    if ctx.consume(K.keyword_token('as')):
      params = fnparams(ctx, parens=False)
    else:
      params = []

    body = block(ctx)
    return A.with_node(func, params, body)

  if ctx.consume(K.keyword_token('while')):
    pred = binexpr(ctx)
    body = block(ctx)
    return A.while_node(pred, body)

  if ctx.consume(K.keyword_token('until')):
    pred = binexpr(ctx)
    body = block(ctx)
    return A.until_node(pred, body)

  if ctx.consume(K.keyword_token('loop')):
    body = block(ctx)
    return A.loop_node(body)

  if ctx.consume(K.keyword_token('pass')):
    return A.pass_node()

  if ctx.consume(K.keyword_token('break')):
    if ctx.consume(K.keyword_token('if')):
      return A.break_node(binexpr(ctx))

    return A.break_node()

  if ctx.consume(K.keyword_token('continue')):
    if ctx.consume(K.keyword_token('if')):
      return A.cont_node(binexpr(ctx))

    return A.cont_node()

  if ctx.consume(K.keyword_token('return')):
    if ctx.expect(newline):
      return A.return_node()

    return A.return_node(compound(ctx))

  if ctx.consume(K.keyword_token('save')):
    return A.save_node(compound(ctx))

  lhs = assn_prefix(ctx)

  if ctx.consume(K.symbol_token('=')):
    rhs = compound(ctx)
    return A.assn_node(lhs, rhs, let=False)

  if ctx.expect(K.symbol_token('(')):
    args = fnargs(ctx)
    return A.call_node(lhs, args)

  if ctx.consume(K.symbol_token(':')):
    name = ctx.require(K.name_token).value
    rhs = A.str_node(name)
    args = fnargs(ctx)
    return A.meth_node(lhs, rhs, args)


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

# let_prefix :: '[' let_prefix (',' let_prefix)* ']'
#             | NAME
def let_prefix(ctx):
  if ctx.consume(K.symbol_token('[')):
    lst = []
    lst.append(let_prefix(ctx))
    while not ctx.consume(K.symbol_token(']')):
      ctx.require(K.symbol_token(','))
      lst.append(let_prefix(ctx))

    return lst

  return A.name_node(ctx.require(K.name_token).value)


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

  return [key, val]


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


# fnargblock :: INDENT (compound NEWLINE)+ DEDENT
def fnargblock(ctx):
  exprs = []
  ctx.require(indent)

  while not ctx.expect(dedent):
    exprs.append(compound(ctx))
    ctx.require(newline)

  ctx.require(dedent)

  return exprs


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


# compound :: macro_exp
#           | 'func' (NAME | STRING)? fnparams ('->' binexpr | block)
#           | binexpr
def compound(ctx):
  if ctx.expect(K.symbol_token('@')):
    return macro_exp(ctx)

  if ctx.consume(K.keyword_token('func')):
    rename = None
    if ctx.expect(K.name_token, K.string_token):
      rename = ctx.require(K.name_token, K.string_token).value

    params = fnparams(ctx)

    if ctx.consume(K.operator_token('->')):
      exp = binexpr(ctx)
      return A.func_node(params, A.return_node(exp))

    body = block(ctx)
    return A.func_node(params, body, rename)

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
    elif nop in rassoc and binary_ops[nop] == binary_ops[op]:
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


# simple :: 'func' fnparams '->' binexpr
#         | 'foreign' (NAME | STRING) fnparams
#         | array_expr
#         | dict_expr
#         | primary
def simple(ctx):
  if ctx.consume(K.keyword_token('func')):
    params = fnparams(ctx)
    ctx.require(K.operator_token('->'))
    exp = binexpr(ctx)
    return A.func_node(params, A.return_node(exp))

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
      rhs = binexpr(ctx)
      ctx.require(K.symbol_token(']'))
      node = A.idx_node(node, rhs)
      continue

    break

  return node


# prefix :: '(' binexpr ')'
#         | NAME | INT | FLOAT | BOOL | STRING | NULL | TABLE
def prefix(ctx):
  if ctx.consume(K.symbol_token('(')):
    node = binexpr(ctx)
    ctx.require(K.symbol_token(')'))
    return node

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
    return A.table_node()

  return A.name_node(ctx.require(K.name_token).value)
