from llvmlite import ir
from .ast import *
from . import types as T
from . import token as K
from collections import OrderedDict

BOX_SIZE = 24

# structure

@program_node.method
def emit(self, module):
  module.metatable_key = module.add_global(T.box)
  module.metatable_key.initializer = str_node('metatable').emit(module)

  for stmt in self.stmts:
    stmt.emit(module)

  if 'main' in module:
    with module.add_main():
      box = module.builder.load(module['main'], name='main_box')
      func = module.builder.extract_value(box, 1, name='main_func')
      ret_ptr = module.builder.alloca(T.box, name='ret_ptr')
      func_ptr = module.builder.inttoptr(func, T.ptr(T.vfunc(T.ptr(T.box))), name='main_func_ptr')
      module.builder.call(func_ptr, [ret_ptr])
      ret_code = module.builder.call(module.extern('rain_box_to_exit'), [ret_ptr], name='ret_code')
      module.builder.ret(ret_code);

@block_node.method
def emit(self, module):
  for stmt in self.stmts:
    stmt.emit(module)

# helpers

def truthy(module, box):
  typ = module.builder.extract_value(box, 0)
  val = module.builder.extract_value(box, 1)
  not_null = module.builder.icmp_unsigned('!=', typ, T.ityp.null)
  not_zero = module.builder.icmp_unsigned('!=', val, T.i64(0))
  return module.builder.and_(not_null, not_zero)

# statements

@assn_node.method
def emit(self, module):
  ptr = None

  if isinstance(self.lhs, name_node):

    if not module.builder:
      module[self.lhs] = module.add_global(T.box)
      module[self.lhs].initializer = self.rhs.emit(module)
      return

    rhs = self.rhs.emit(module) # emit this so a function can't close over its undefined binding

    if self.let:
      module[self.lhs] = module.builder.alloca(T.box)

    if self.lhs not in module:
      raise Exception('Undeclared {!r}'.format(self.lhs))

    module.builder.store(rhs, module[self.lhs])

  elif isinstance(self.lhs, idx_node):
    table = self.lhs.lhs.emit(module)
    key = self.lhs.rhs.emit(module)
    val = self.rhs.emit(module)

    table_ptr = module.builder.alloca(T.box, name='table_ptr')
    key_ptr = module.builder.alloca(T.box, name='key_ptr')
    val_ptr = module.builder.alloca(T.box, name='val_ptr')

    module.builder.store(table, table_ptr)
    module.builder.store(key, key_ptr)
    module.builder.store(val, val_ptr)

    module.builder.call(module.extern('rain_put'), [table_ptr, key_ptr, val_ptr])

@break_node.method
def emit(self, module):
  if not self.cond:
    return module.builder.branch(module.after)

  cond = truthy(module, self.cond.emit(module))
  nobreak = module.builder.append_basic_block('nobreak')
  module.builder.cbranch(cond, module.after, nobreak)
  module.builder.position_at_end(nobreak)

@cont_node.method
def emit(self, module):
  if not self.cond:
    return module.builder.branch(module.before)

  cond = truthy(module, self.cond.emit(module))
  nocont = module.builder.append_basic_block('nocont')
  module.builder.cbranch(cond, module.before, nocont)
  module.builder.position_at_end(nocont)

@if_node.method
def emit(self, module):
  pred = truthy(module, self.pred.emit(module))

  if self.els:
    with module.builder.if_else(pred) as (then, els):
      with then:
        self.body.emit(module)
      with els:
        self.els.emit(module)

  else:
    with module.builder.if_then(truthy(module, self.pred.emit(module))):
      self.body.emit(module)

@loop_node.method
def emit(self, module):
  with module.add_loop() as (before, loop):
    with before:
      module.builder.branch(module.loop)

    with loop:
      self.body.emit(module)
      module.builder.branch(module.loop)

@pass_node.method
def emit(self, module):
  pass

@return_node.method
def emit(self, module):
  if self.value:
    ret = self.value
  else:
    ret = null_node()

  module.builder.store(ret.emit(module), module.ret_ptr)
  module.builder.ret_void()

@print_node.method
def emit(self, module):
  val = self.value.emit(module)
  val_ptr = module.builder.alloca(T.box, name='val_ptr')
  module.builder.store(val, val_ptr)
  module.builder.call(module.extern('rain_print'), [val_ptr])

@until_node.method
def emit(self, module):
  with module.add_loop() as (before, loop):
    with before:
      module.builder.cbranch(truthy(module, self.pred.emit(module)), module.after, module.loop)

    with loop:
      self.body.emit(module)
      module.builder.branch(module.before)

@while_node.method
def emit(self, module):
  with module.add_loop() as (before, loop):
    with before:
      module.builder.cbranch(truthy(module, self.pred.emit(module)), module.loop, module.after)

    with loop:
      self.body.emit(module)
      module.builder.branch(module.before)

@for_node.method
def emit(self, module):
  # evaluate the expression and pull out the function pointer
  func_box = self.func.emit(module)
  func_raw = module.builder.extract_value(func_box, 1, name='for_func')
  func_ptr = module.builder.inttoptr(func_raw, T.ptr(T.vfunc(T.ptr(T.box))), name='for_func_ptr')

  # set up the return pointer
  ret_ptr = module[self.name] =  module.builder.alloca(T.box, name='for_var')
  module.builder.store(T.box(None), ret_ptr)

  with module.add_loop() as (before, loop):
    with before:
      # call our function and break if it returns null
      module.builder.call(func_ptr, [ret_ptr])
      box = module.builder.load(ret_ptr)
      typ = module.builder.extract_value(box, 0)
      not_null = module.builder.icmp_unsigned('!=', typ, T.ityp.null)
      module.builder.cbranch(not_null, module.loop, module.after)

    with loop:
      self.body.emit(module)
      module.builder.branch(module.before)

# expressions

@name_node.method
def emit(self, module):
  if self.value not in module:
    raise Exception('Unknown {!r}'.format(self.value))

  return module.builder.load(module[self.value])

@idx_node.method
def emit(self, module):
  table = self.lhs.emit(module)
  key = self.rhs.emit(module)

  ret_ptr = module.builder.alloca(T.box, name='ret_ptr')
  table_ptr = module.builder.alloca(T.box, name='table_ptr')
  key_ptr = module.builder.alloca(T.box, name='key_ptr')

  module.builder.store(table, table_ptr)
  module.builder.store(key, key_ptr)
  module.builder.call(module.extern('rain_get'), [ret_ptr, table_ptr, key_ptr])

  return module.builder.load(ret_ptr)

@null_node.method
def emit(self, module):
  return T.box([T.ityp.null, T.cast.null(0), T.i32(0)])

@int_node.method
def emit(self, module):
  return T.box([T.ityp.int, T.cast.int(self.value), T.i32(0)])

@float_node.method
def emit(self, module):
  val = T.cast.float(self.value).bitcast(T.cast.int)
  return T.box([T.ityp.float, val, T.i32(0)])

@bool_node.method
def emit(self, module):
  return T.box([T.ityp.bool, T.cast.bool(int(self.value)), T.i32(0)])

@str_node.method
def emit(self, module):
  typ = T.arr(T.i8, len(self.value) + 1)
  ptr = module.add_global(typ, name=module.uniq('string'))
  ptr.initializer = typ(bytearray(self.value + '\0', 'utf-8'))
  gep = ptr.gep([T.i32(0), T.i32(0)])

  # need to bullshit around to get this to work - see llvmlite#229
  raw_ir = 'ptrtoint ({0} {1} to {2})'.format(gep.type, gep.get_reference(), T.cast.int)
  val = ir.FormattedConstant(T.cast.int, raw_ir)
  return T.box([T.ityp.str, val, len(self.value)])

@table_node.method
def emit(self, module):
  ptr = module.builder.call(module.extern('rain_new_table'), [])

  if self.metatable:
    val = self.metatable.emit(module)
    val_ptr = module.builder.alloca(T.box, name='key_ptr')
    module.builder.store(val, val_ptr)
    module.builder.call(module.extern('rain_put'), [ptr, module.metatable_key, val_ptr])

  return module.builder.load(ptr)

@func_node.method
def emit(self, module):
  env = OrderedDict()
  for scope in module.scopes[1:]:
    for nm, ptr in scope.items():
      env[nm] = ptr

  if not env:
    typ = T.vfunc(T.ptr(T.box), *[T.ptr(T.box) for x in self.params])

    func = module.add_func(typ)
    func.args[0].add_attribute('sret')

  else:
    env_typ = T.arr(T.box, len(env))
    typ = T.vfunc(T.ptr(env_typ), T.ptr(T.box), *[T.ptr(T.box) for x in self.params])

    func = module.add_func(typ)
    func.args[0].add_attribute('nest')
    func.args[1].add_attribute('sret')

  with module:
    with module.add_func_body(func):
      func_args = func.args

      if env:
        for i, (name, ptr) in enumerate(env.items()):
          gep = module.builder.gep(func_args[0], [T.i32(0), T.i32(i)])
          module[name] = gep

        func_args = func_args[1:]
        module.ret_ptr = func.args[1]

      for name, ptr in zip(self.params, func_args[1:]):
        module[name] = ptr

      self.body.emit(module)

      if not module.builder.block.is_terminated:
        module.builder.store(null_node().emit(module), module.ret_ptr)
        module.builder.ret_void()

  if env:
    env_raw_ptr = module.builder.call(module.extern('GC_malloc'), [T.i32(BOX_SIZE * len(env))])
    env_ptr = module.builder.bitcast(env_raw_ptr, T.ptr(env_typ))
    env_val = env_typ(None)
    for i, (name, ptr) in enumerate(env.items()):
      env_val = module.builder.insert_value(env_val, module.builder.load(ptr), i)
    module.builder.store(env_val, env_ptr)

    func = module.add_tramp(func, env_ptr)
    func_i64 = module.builder.ptrtoint(func, T.i64)

    return module.builder.insert_value(T.box([T.ityp.func, T.i64(0), T.i32(0)]), func_i64, 1)

  #val = func.ptrtoint(T.cast.int)
  # need to bullshit around to get this to work - see llvmlite#229
  raw_ir = 'ptrtoint ({0} {1} to {2})'.format(func.type, func.get_reference(), T.cast.int)
  val = ir.FormattedConstant(T.cast.int, raw_ir)
  return T.box([T.ityp.func, val, T.i32(0)])

@extern_node.method
def emit(self, module):
  typ = T.vfunc()
  func = module.find_func(typ, name=self.name.value)

  raw_ir = 'ptrtoint ({0} {1} to {2})'.format(func.type, func.get_reference(), T.cast.int)
  val = ir.FormattedConstant(T.cast.int, raw_ir)
  return T.box([T.ityp.func, val, T.i32(0)])

@call_node.method
def emit(self, module):
  func_box = self.func.emit(module)
  arg_boxes = [arg.emit(module) for arg in self.args]
  arg_ptrs = [module.builder.alloca(T.box) for arg in arg_boxes]

  for box, ptr in zip(arg_boxes, arg_ptrs):
    module.builder.store(box, ptr)

  ret_ptr = module.builder.alloca(T.box, name='ret_ptr')
  module.builder.store(T.box(None), ret_ptr)

  func = module.builder.extract_value(func_box, 1, name='func')
  func_ptr = module.builder.inttoptr(func, T.ptr(T.vfunc(T.ptr(T.box), *[T.ptr(T.box) for arg in arg_ptrs])))

  module.builder.call(func_ptr, [ret_ptr] + arg_ptrs)
  ret = module.builder.load(ret_ptr)

  return ret

@meth_node.method
def emit(self, module):
  table = self.lhs.emit(module)
  key = self.rhs.emit(module)

  ret_ptr = module.builder.alloca(T.box, name='ret_ptr')
  table_ptr = module.builder.alloca(T.box, name='table_ptr')
  key_ptr = module.builder.alloca(T.box, name='key_ptr')

  module.builder.store(table, table_ptr)
  module.builder.store(key, key_ptr)
  module.builder.call(module.extern('rain_get'), [ret_ptr, table_ptr, key_ptr])
  func_box = module.builder.load(ret_ptr)

  #

  arg_boxes = [arg.emit(module) for arg in self.args]
  arg_ptrs = [module.builder.alloca(T.box) for arg in arg_boxes]

  for box, ptr in zip(arg_boxes, arg_ptrs):
    module.builder.store(box, ptr)

  arg_ptrs = [table_ptr] + arg_ptrs

  ret_ptr = module.builder.alloca(T.box, name='ret_ptr')
  module.builder.store(T.box(None), ret_ptr)

  func = module.builder.extract_value(func_box, 1, name='func')
  func_ptr = module.builder.inttoptr(func, T.ptr(T.vfunc(T.ptr(T.box), *[T.ptr(T.box) for arg in arg_ptrs])))

  module.builder.call(func_ptr, [ret_ptr] + arg_ptrs)
  ret = module.builder.load(ret_ptr)

  return ret

@binary_node.method
def emit(self, module):
  arith = {
    '+': 'rain_add',
    '-': 'rain_sub',
    '*': 'rain_mul',
    '/': 'rain_div',
    '&': 'rain_and',
    '|': 'rain_or',
    '==': 'rain_eq',
    '!=': 'rain_ne',
    '>': 'rain_gt',
    '>=': 'rain_ge',
    '<': 'rain_lt',
    '<=': 'rain_le',
  }

  lhs = self.lhs.emit(module)
  rhs = self.rhs.emit(module)
  lhs_ptr = module.builder.alloca(T.box, name='lhs_ptr')
  rhs_ptr = module.builder.alloca(T.box, name='rhs_ptr')
  ret_ptr = module.builder.alloca(T.box, name='ret_ptr')
  module.builder.store(lhs, lhs_ptr)
  module.builder.store(rhs, rhs_ptr)
  module.builder.store(T.box(None), ret_ptr)
  module.builder.call(module.extern(arith[self.op]), [ret_ptr, lhs_ptr, rhs_ptr])
  return module.builder.load(ret_ptr)

@unary_node.method
def emit(self, module):
  arith = {
    '-': 'rain_neg',
    '!': 'rain_not',
  }

  val = self.val.emit(module)
  val_ptr = module.builder.alloca(T.box, name='val_ptr')
  ret_ptr = module.builder.alloca(T.box, name='ret_ptr')
  module.builder.store(val, val_ptr)
  module.builder.store(T.box(None), ret_ptr)
  module.builder.call(module.extern(arith[self.op]), [ret_ptr, val_ptr])
  return module.builder.load(ret_ptr)

@is_node.method
def emit(self, module):
  lhs = self.lhs.emit(module)
  lhs_typ = module.builder.extract_value(lhs, 0)
  res = module.builder.icmp_unsigned('==', getattr(T.ityp, self.typ.value), lhs_typ)
  res = module.builder.zext(res, T.i64)
  return module.builder.insert_value(T.box([T.ityp.bool, T.i64(0), T.i32(0)]), res, 1)
