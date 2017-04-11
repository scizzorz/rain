from . import compiler as C
from . import module as M
from . import types as T
from . import error as Q
from .ast import *
from collections import OrderedDict
from llvmlite import ir
import os.path


# Program structure ###########################################################

@program_node.method
def emit(self, module):
  module.exports = module.add_global(T.box, name=module.mangle('exports'))
  module.exports.initializer = module.static.alloc(name=module.mangle('exports.table'))

  for stmt in self.stmts:
    module.emit(stmt)


@program_node.method
def emit_main(self, module, mods=[]):
  with module.add_func_body(module.main):
    ret_ptr = module.alloc(T.null, name='ret_ptr')

    with module.add_abort():
      module.runtime.init_gc()
      module.runtime.init_args(*module.main.args)

      for tmp in mods:
        if 'init' in tmp:
          with tmp.borrow_builder(module):
            init_box = tmp.load_global('init')

          init_ptr = module.get_value(init_box, typ=T.vfunc(T.arg))
          module.check_callable(init_box, 0, unwind=module.catch)
          module.store(T.null, ret_ptr) # necessary?
          module.call(init_ptr, ret_ptr, unwind=module.catch)

      module.runtime.main(ret_ptr, module['main'], unwind=module.catch)

      module.catch_and_abort(module.builder.block)

      ret_code = module.runtime.box_to_exit(ret_ptr)
      module.builder.ret(ret_code)


@block_node.method
def emit(self, module):
  for stmt in self.stmts:
    module.emit(stmt)

  if self.expr:
    return module.emit(self.expr)

  return T.null


# Helpers #####################################################################

# flatten arbitrarily nested lists
def flatten(items):
  for x in items:
    if isinstance(x, list):
      yield from flatten(x)
    else:
      yield x

# Simple statements ###########################################################

@assn_node.method
def emit(self, module):
  if isinstance(self.lhs, list): # unpack
    if module.is_global:
      # to avoid making this code hideous for the time being
      # theoretically, there's no reason for this
      Q.abort("Unable to unpack at global scope")

    # evalute the RHS before storing anything
    deep_rhs = module.emit(self.rhs)
    flat_rhs = flatten(module.unpack(deep_rhs, self.lhs))
    flat_lhs = flatten(self.lhs)

    # store everything
    for lhs, rhs in zip(flat_lhs, flat_rhs):
      if isinstance(lhs, name_node):
        if self.let:
          with module.goto_entry():
            module[lhs] = module.alloc()
            module[lhs].bound = False

        if lhs not in module:
          Q.abort("Undeclared name {!r}", lhs.value, pos=lhs.coords)

        module[lhs].bound = True
        module.store(rhs, module[lhs])

      elif isinstance(lhs, idx_node):
        table = module.emit(lhs.lhs)
        key = module.emit(lhs.rhs)
        args = module.fnalloc(table, key, rhs)
        module.runtime.put(*args)

  elif isinstance(self.lhs, name_node):
    if module.is_global:
      if self.export:
        table_box = module.exports.initializer
        key_node = str_node(self.lhs.value)
        module[self.lhs.value] = module.static.get_box_ptr(table_box, key_node)

      if self.let:
        module[self.lhs] = module.find_global(T.box, name=module.mangle(self.lhs.value))
        module[self.lhs].linkage = '' # make sure we know it's visible here

      if self.lhs not in module:
        Q.abort("Undeclared global {!r}", self.lhs.value, pos=self.lhs.coords)

      module.store_global(module.emit(self.rhs), self.lhs.value)
      return

    if self.let:
      with module.goto_entry():
        module[self.lhs] = module.alloc()
        module[self.lhs].bound = False  # cheesy hack - see @func_node

    rhs = module.emit(self.rhs)

    if self.lhs not in module:
      Q.abort("Undeclared name {!r}", self.lhs.value, pos=self.lhs.coords)

    module[self.lhs].bound = True
    module.store(rhs, module[self.lhs])

  elif isinstance(self.lhs, idx_node):
    if module.is_global:
      table_box = module.emit(self.lhs.lhs)
      key_node = self.lhs.rhs
      val = module.emit(self.rhs)

      module.static.put(table_box, key_node, val)
      return

    table = module.emit(self.lhs.lhs)
    key = module.emit(self.lhs.rhs)
    val = module.emit(self.rhs)

    args = module.fnalloc(table, key, val)
    module.runtime.put(*args)


@break_node.method
def emit(self, module):
  if not self.cond:
    return module.builder.branch(module.after)

  cond = module.truthy(self.cond)
  nobreak = module.builder.append_basic_block('nobreak')
  module.builder.cbranch(cond, module.after, nobreak)
  module.builder.position_at_end(nobreak)


@cont_node.method
def emit(self, module):
  if not self.cond:
    return module.builder.branch(module.before)

  cond = module.truthy(self.cond)
  nocont = module.builder.append_basic_block('nocont')
  module.builder.cbranch(cond, module.before, nocont)
  module.builder.position_at_end(nocont)


@export_foreign_node.method
def emit(self, module):
  if module.is_local:
    Q.abort("Can't export value {!r} as foreign at non-global scope", self.name, pos=self.coords)

  if self.name not in module:
    Q.abort("Can't export unknown name {!r}", self.name, self.rename, pos=self.coords)

  glob = module.add_global(T.ptr(T.box), name=self.rename)
  glob.initializer = module[self.name]


@import_node.method
def emit(self, module):
  # add the module's directory to the lookup path
  if getattr(module, 'file', None):
    base, name = os.path.split(module.file)
    file = M.find_rain(self.name, paths=[base])
  else:
    file = M.find_rain(self.name)

  if not file:
    Q.abort("Can't find module {!r}", self.name, pos=self.coords)

  comp = C.get_compiler(file)
  comp.build()

  module.import_llvm(comp.mod)
  glob = module.get_global(comp.mod.mangle('exports.table'))
  #glob.arr_ptr = module.get_global(comp.mod.mangle('exports.table.array'))

  rename = self.rename or comp.mname

  module[rename] = module.find_global(T.box, module.mangle(rename))
  module[rename].linkage = '' # make sure we know it's visible here

  module[rename].initializer = module.static.from_ptr(glob)
  module[rename].mod = comp.mod
  module.imports.add(file)


@link_node.method
def emit(self, module):
  base, name = os.path.split(module.file)
  file = M.find_file(self.name, paths=[base])
  module.links.add(file)


@lib_node.method
def emit(self, module):
  module.libs.add(self.name)


@macro_node.method
def emit(self, module):
  pass


@macro_node.method
def expand(self, module, name):
  typ = T.vfunc(T.arg, *[T.arg for x in self.params])

  func_node(self.params, self.body, 'macro.func.real:' + name).emit(module)
  real_func = module.find_func(typ, 'macro.func.real:' + name)

  main_func = module.add_func(typ, name='macro.func.main:' + name)
  main_func.attributes.personality = module.personality
  main_func.args[0].add_attribute('sret')
  with module.add_func_body(main_func):
    with module.add_abort():
      module.call(real_func, *main_func.args, unwind=module.catch)
      module.catch_and_abort(module.builder.block)

    module.builder.ret_void()


@pass_node.method
def emit(self, module):
  pass


@return_node.method
def emit(self, module):
  if self.value:
    module.store(module.emit(self.value), module.ret_ptr)

  module.builder.ret_void()


@save_node.method
def emit(self, module):
  module.store(module.emit(self.value), module.ret_ptr)

# Block statements ############################################################


@if_node.method
def emit(self, module):
  pred = module.truthy(self.pred)

  if self.els:
    with module.builder.if_else(pred) as (then, els):
      with then:
        module.emit(self.body)
      with els:
        module.emit(self.els)

  else:
    with module.builder.if_then(pred):
      module.emit(self.body)


@with_node.method
def emit(self, module):
  user_box = module.emit(self.expr)
  user_ptr = module.get_value(user_box, typ=T.vfunc(T.arg, T.arg))
  module.check_callable(user_box, 1)

  func_box = module.emit(func_node(self.params, self.body))

  ptrs = module.fnalloc(T.null, func_box)

  env = module.get_env(user_box)
  has_env = module.builder.icmp_unsigned('!=', env, T.arg(None))
  with module.builder.if_then(has_env):
    env_box = module.load(env)
    module.store(env_box, ptrs[0])

  module.call(user_ptr, *ptrs)


@loop_node.method
def emit(self, module):
  with module.add_loop():
    with module.goto(module.before):
      module.builder.branch(module.loop)

    with module.goto(module.loop):
      module.emit(self.body)
      module.builder.branch(module.loop)


@until_node.method
def emit(self, module):
  with module.add_loop():
    with module.goto(module.before):
      module.builder.cbranch(module.truthy(self.pred), module.after, module.loop)

    with module.goto(module.loop):
      module.emit(self.body)
      module.builder.branch(module.before)


@while_node.method
def emit(self, module):
  with module.add_loop():
    with module.goto(module.before):
      module.builder.cbranch(module.truthy(self.pred), module.loop, module.after)

    with module.goto(module.loop):
      module.emit(self.body)
      module.builder.branch(module.before)


@for_node.method
def emit(self, module):
  # evaluate the expressions and pull out the function pointers
  func_box = module.emit(self.func)
  module.check_callable(func_box, 0)

  func_ptr = module.get_value(func_box, T.vfunc(T.arg))
  func_env = module.get_env(func_box)
  has_env = module.builder.icmp_unsigned('!=', func_env, T.arg(None))

  # set up the return pointers
  with module.goto_entry():
    ret_ptr = module.alloc()
    if isinstance(self.name, name_node):
      module[self.name.value] = ret_ptr
    elif isinstance(self.name, list):
      for name in flatten(self.name):
        module[name.value] = module.alloc()

  with module.add_loop():
    with module.goto(module.before):
      module.store(T.null, ret_ptr)

      with module.builder.if_then(has_env):
        env_box = module.load(func_env)
        module.store(env_box, ret_ptr)

      module.call(func_ptr, ret_ptr)
      box = module.load(ret_ptr)
      typ = module.get_type(box)

      not_null = module.builder.icmp_unsigned('!=', typ, T.ityp.null)
      module.builder.cbranch(not_null, module.loop, module.after)

    with module.goto(module.loop):
      if isinstance(self.name, list):
        flat_lhs = flatten(self.name)
        flat_rhs = flatten(module.unpack(module.load(ret_ptr), self.name))

        for lhs, rhs in zip(flat_lhs, flat_rhs):
          module.store(rhs, module[lhs.value])

      module.emit(self.body)
      module.builder.branch(module.before)


@catch_node.method
def emit(self, module):
  with module.goto_entry():
    ret_ptr = module[self.name] = module.alloc(T.null, name='exc_var')

  end = module.builder.append_basic_block('end_catch')

  with module.add_catch(True):
    module.emit(self.body)
    module.catch_into(ret_ptr, end)

  module.builder.branch(end)
  module.builder.position_at_end(end)


# Simple expressions ##########################################################

@name_node.method
def emit(self, module):
  if self.value not in module:
    Q.abort("Unknown name {!r}", self.value, pos=self.coords)

  if module.is_global:
    return module.load_global(self.value)

  return module.load(module[self.value])


@null_node.method
def emit(self, module):
  return T.null


@int_node.method
def emit(self, module):
  return T._int(self.value, module.get_vt('int'))


@float_node.method
def emit(self, module):
  return T._float(self.value, module.get_vt('float'))


@bool_node.method
def emit(self, module):
  return T._bool(self.value, module.get_vt('bool'))


@str_node.method
def emit(self, module):
  typ = T.arr(T.i8, len(self.value) + 1)
  ptr = module.add_global(typ, name=module.uniq('string'))
  ptr.initializer = typ(bytearray(self.value + '\0', 'utf-8'))
  gep = ptr.gep([T.i32(0), T.i32(0)])

  return T._str(gep, len(self.value), module.get_vt('str'))


@table_node.method
def emit(self, module):
  if module.is_global:
    return module.static.alloc(module.uniq('table'))

  ptr = module.runtime.new_table()
  return module.load(ptr)


@array_node.method
def emit(self, module):
  if module.is_global:
    table_box = module.static.alloc(module.uniq('array'))

    for i, item in enumerate(self.items):
      key_node = int_node(i)
      val = module.emit(item)

      module.static.put(table_box, key_node, val)

    old_box = table_box
    table_box = T.insertvalue(table_box, module.get_vt('array'), T.ENV)
    module.static.repair(table_box, old_box)

    return table_box

  ptr = module.runtime.new_table()
  for i, item in enumerate(self.items):
    args = module.fnalloc(int_node(i).emit(module), module.emit(item))
    module.runtime.put(ptr, *args)

  ret = module.load(ptr)
  ret = module.insert(ret, module.get_vt('array'), T.ENV)

  return ret


@dict_node.method
def emit(self, module):
  if module.is_global:
    table_box = module.static.alloc(module.uniq('array'))

    for key, item in self.items:
      key_node = key
      val = module.emit(item)

      module.static.put(table_box, key_node, val)

    old_box = table_box
    table_box = T.insertvalue(table_box, module.get_vt('dict'), T.ENV)
    module.static.repair(table_box, old_box)

    return table_box

  ptr = module.runtime.new_table()
  for key, item in self.items:
    args = module.fnalloc(module.emit(key), module.emit(item))
    module.runtime.put(ptr, *args)

  ret = module.load(ptr)
  ret = module.insert(ret, module.get_vt('dict'), T.ENV)

  return ret


@func_node.method
def emit(self, module):
  env = OrderedDict()
  for scope in module.scopes[1:]:
    for nm, ptr in scope.items():
      env[nm] = ptr

  env_typ = T.arr(T.box, len(env))
  typ = T.vfunc(T.arg, *[T.arg for x in self.params])

  func = module.add_func(typ, name=self.rename)
  func.attributes.personality = module.personality
  func.args[0].add_attribute('sret')

  with module:
    with module.add_func_body(func):
      if env:
        with module.goto_entry():
          key_ptr = module.alloc()

        #env_box = module.load(func.args[0])
        env_ptr = func.args[0]

        for i, (name, ptr) in enumerate(env.items()):
          module.store(str_node(name).emit(module), key_ptr)
          module[name] = module.runtime.get_ptr(env_ptr, key_ptr)

        module.store(T.null, func.args[0])

      for name, ptr in zip(self.params, func.args[1:]):
        module[name] = ptr

      module.emit(self.body)

      if not module.builder.block.is_terminated:
        module.builder.ret_void()

  func_box = T._func(func, len(self.params))

  if env:
    env_ptr = module.runtime.new_table()

    func_box = module.insert(func_box, env_ptr, T.ENV)

    with module.goto_entry():
      key_ptr = module.alloc()
      self_ptr = module.alloc()

    module.store(func_box, self_ptr)

    for i, (name, ptr) in enumerate(env.items()):
      # cheesy hack - the only time any of these values will ever
      # have a bound value of False will be when it's the item
      # currently being bound, ie, it's this function
      module.store(str_node(name).emit(module), key_ptr)
      if getattr(ptr, 'bound', None) is False:
        module.runtime.put(env_ptr, key_ptr, self_ptr)
      else:
        module.runtime.put(env_ptr, key_ptr, ptr)

  return func_box


@foreign_node.method
def emit(self, module):
  typ = T.vfunc(*[T.arg for param in self.params])
  func = module.find_func(typ, name=self.name)
  return T._func(func, len(self.params))


# Compound expressions ########################################################

@call_node.method
def emit(self, module):
  if module.is_global:
    Q.abort("Can't call functions at global scope", pos=self.coords)

  func_box = module.emit(self.func)
  arg_boxes = [module.emit(arg) for arg in self.args]

  return module.box_call(func_box, arg_boxes, catch=self.catch)


@meth_node.method
def emit(self, module):
  if module.is_global:
    Q.abort("Can't call methods at global scope", pos=self.coords)

  table = module.emit(self.lhs)
  key = module.emit(self.rhs)

  ret_ptr, *args = module.fnalloc(T.null, table, key)
  module.runtime.get(ret_ptr, *args)

  func_box = module.load(ret_ptr)
  arg_boxes = [table] + [module.emit(arg) for arg in self.args]

  return module.box_call(func_box, arg_boxes, catch=self.catch)


@idx_node.method
def emit(self, module):
  if module.is_global:
    # check if LHS is a module
    if getattr(module[self.lhs], 'mod', None):
      return module[self.lhs].mod.load_global(self.rhs)

    # otherwise, do normal lookups
    table_box = module.emit(self.lhs)
    key_node = self.rhs

    return module.static.get(table_box, key_node)

  table = module.emit(self.lhs)
  key = module.emit(self.rhs)

  ret_ptr, *args = module.fnalloc(T.null, table, key)
  module.runtime.get(ret_ptr, *args)
  return module.load(ret_ptr)


# Operator expressions ########################################################

@unary_node.method
def emit(self, module):
  if module.is_global:
    Q.abort("Can't use unary operators at global scope", pos=self.coords)

  arith = {
    '-': module.runtime.neg,
    '!': module.runtime.lnot,
  }

  val = module.emit(self.val)

  ret_ptr, arg = module.fnalloc(T.null, val)
  arith[self.op](ret_ptr, arg)

  return module.load(ret_ptr)


@binary_node.method
def emit(self, module):
  if self.op == '::':
    lhs = module.emit(self.lhs)
    rhs = module.emit(self.rhs)

    if module.is_global:
      ptr = module.add_global(T.box)
      ptr.initializer = rhs

      new_lhs = T.insertvalue(lhs, ptr, T.ENV)
      module.static.repair(new_lhs, lhs)

      return new_lhs

    ptr = module.runtime.box_malloc()
    module.store(rhs, ptr)
    return module.insert(lhs, ptr, T.ENV)

  if module.is_global:
    Q.abort("Can't use binary operators at global scope", pos=self.coords)

  if self.op in ('|', '&'):
    with module.goto_entry():
      res = module.alloc()

    lhs = module.emit(self.lhs)
    module.store(lhs, res)

    t = module.truthy_val(lhs)
    if self.op == '|':
      t = module.builder.not_(t)

    with module.builder.if_then(t):
      rhs = module.emit(self.rhs)
      module.store(rhs, res)

    return module.load(res)

  arith = {
    '+': module.runtime.add,
    '-': module.runtime.sub,
    '*': module.runtime.mul,
    '/': module.runtime.div,
    '==': module.runtime.eq,
    '!=': module.runtime.ne,
    '>': module.runtime.gt,
    '>=': module.runtime.ge,
    '<': module.runtime.lt,
    '<=': module.runtime.le,
    '$': module.runtime.string_concat,
  }

  if self.op not in arith:
    Q.abort("Invalid binary operator {!r}", self.op, pos=self.coords)

  lhs = module.emit(self.lhs)
  rhs = module.emit(self.rhs)

  ret_ptr, *args = module.fnalloc(T.null, lhs, rhs)
  arith[self.op](ret_ptr, *args)

  return module.load(ret_ptr)


# Warning statements ##########################################################

@error_node.method
def emit(self, module):
  Q.abort(self.msg)


@warning_node.method
def emit(self, module):
  Q.warn(self.msg)


@hint_node.method
def emit(self, module):
  Q.hint(self.msg)
