from . import ast as A
from . import compiler as C
from . import error as Q
from . import module as M
from . import token as K
from . import types as T
import os.path


# flatten arbitrarily nested lists
# oh come on what is this doing here go find a new home
def flatten(items):
  for x in items:
    if isinstance(x, list):
      yield from flatten(x)
    else:
      yield x


# Program structure ###########################################################

@A.program_node.method
def emit(self, module):
  module['module'] = module.find_global(T.box, name=module.mangle('module'))
  module['module'].initializer = T.null
  module['module'].linkage = ''

  for stmt in self.stmts:
    module.emit(stmt)


@A.program_node.method
def emit_main(self, module, mods=[]):
  with module.add_func_body(module.runtime.main):
    with module.add_catch():
      module.runtime.init_gc()
      module.runtime.init_args(*module.runtime.main.args)

      for tmp in mods:
        if 'init' in tmp:
          with module.trace(K.coord(M.TRACE_INIT), mod=tmp.name_ptr):
            module.box_call(module.load(tmp['init']))

      with module.trace(K.coord(M.TRACE_MAIN)):
        module.box_call(module.load(module['main']))

      module.catch(module.builder.block)

      ret_code = module.runtime.box_to_exit(module.arg_ptrs[0])
      module.builder.ret(ret_code)


@A.block_node.method
def emit(self, module):
  for stmt in self.stmts:
    module.emit(stmt)

  if self.expr:
    return module.emit(self.expr)

  else:
    return T.null


# Simple statements ###########################################################

@A.assn_node.method
def emit_global(self, module):
  if isinstance(self.lhs, list):  # unpack
    # to avoid making this code hideous for the time being
    # theoretically, there's no reason for this
    Q.abort("Unable to unpack at global scope")

  elif isinstance(self.lhs, A.name_node):
    if self.var:
      module[self.lhs] = module.find_global(T.box, name=module.mangle(self.lhs.value))
      module[self.lhs].linkage = ''  # make sure we know it's visible here

    if self.lhs not in module:
      Q.abort("Undeclared global {!r}", self.lhs.value, pos=self.lhs.coords)

    if self.rhs:
      rhs = module.emit(self.rhs)
    else:
      rhs = T.null

    module.store_global(rhs, self.lhs.value)

  elif isinstance(self.lhs, A.idx_node):
    table_box = module.emit(self.lhs.lhs)
    key_node = self.lhs.rhs
    val = module.emit(self.rhs)

    module.static.put(table_box, key_node, val)


@A.assn_node.method
def emit_local(self, module):
  if isinstance(self.lhs, list):  # unpack
    # evalute the RHS before storing anything
    deep_rhs = module.emit(self.rhs)
    flat_rhs = flatten(module.unpack(deep_rhs, self.lhs))
    flat_lhs = flatten(self.lhs)

    # store everything
    for lhs, rhs in zip(flat_lhs, flat_rhs):
      if isinstance(lhs, A.name_node):
        if self.var:
          with module.goto_entry():
            module[lhs] = module.alloc(T.null)
            module[lhs].bound = False

        if lhs not in module:
          Q.abort("Undeclared name {!r}", lhs.value, pos=lhs.coords)

        module[lhs].bound = True
        module.store(rhs, module[lhs])

      elif isinstance(lhs, A.idx_node):
        table = module.emit(lhs.lhs)
        key = module.emit(lhs.rhs)
        args = module.fnalloc(table, key, rhs)
        module.runtime.put(*args)

  elif isinstance(self.lhs, A.name_node):
    if self.var:
      with module.goto_entry():
        module[self.lhs] = module.alloc(T.null)
        module[self.lhs].bound = False  # cheesy hack - see @func_node

    if self.rhs:
      rhs = module.emit(self.rhs)
    else:
      rhs = T.null

    if self.lhs not in module:
      Q.abort("Undeclared name {!r}", self.lhs.value, pos=self.lhs.coords)

    module[self.lhs].bound = True
    module.store(rhs, module[self.lhs])

  elif isinstance(self.lhs, A.idx_node):
    table = module.emit(self.lhs.lhs)
    key = module.emit(self.lhs.rhs)
    val = module.emit(self.rhs)

    args = module.fnalloc(table, key, val)
    module.runtime.put(*args)


@A.bind_node.method
def emit_local(self, module):
  with module.goto_entry():
    key_ptr = module.alloc()

  env_ptr = module.bind_ptr

  for i, name in enumerate(self.names):
    module.store(A.str_node(name).emit(module), key_ptr)
    module[name] = module.runtime.get_ptr(env_ptr, key_ptr)
    module[name].bound = True

    is_null = module.builder.icmp_unsigned('==', module[name], T.arg(None))
    with module.builder.if_then(is_null):
      module.runtime.panic(module.load_exception('unbound_var'))

    module.bindings.add(name)


@A.use_node.method
def emit_global(self, module):
  table_box = module.emit(self.lhs)
  if getattr(table_box, 'mod', None):
    if self.rhs not in table_box.mod:
      Q.abort('Key error', pos=self.coords)

    module[self.name] = table_box.mod[self.rhs]

  else:
    module[self.name] = module.static.get_ptr(table_box, self.rhs)
    if module[self.name] == None:
      Q.abort('Key error', pos=self.coords)


@A.use_node.method
def emit_local(self, module):
  lhs = module.emit(self.lhs)
  rhs = module.emit(self.rhs)
  ptrs = module.fnalloc(lhs, rhs)
  with module.trace(self.coords):
    module[self.name] = module.runtime.get_ptr(*ptrs)

    is_null = module.builder.icmp_unsigned('==', module[self.name], T.arg(None))
    with module.builder.if_then(is_null):
      module.runtime.panic(module.load_exception('key_error'))


@A.break_node.method
def emit(self, module):
  if not self.cond:
    module.builder.branch(module.after)

  else:
    cond = module.truthy(self.cond)
    nobreak = module.builder.append_basic_block('nobreak')
    module.builder.cbranch(cond, module.after, nobreak)
    module.builder.position_at_end(nobreak)


@A.cont_node.method
def emit(self, module):
  if not self.cond:
    module.builder.branch(module.before)

  else:
    cond = module.truthy(self.cond)
    nocont = module.builder.append_basic_block('nocont')
    module.builder.cbranch(cond, module.before, nocont)
    module.builder.position_at_end(nocont)


@A.export_foreign_node.method
def emit_global(self, module):
  if self.name not in module:
    Q.abort("Can't export unknown name {!r}", self.name, pos=self.coords)

  glob = module.add_global(T.ptr(T.box), name=self.rename)
  glob.initializer = module[self.name]


@A.export_foreign_node.method
def emit_local(self, module):
  Q.abort("Can't export as foreign in non-global scope", pos=self.coords)


@A.import_node.method
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

  rename = self.rename or comp.mname

  module[rename] = module.find_global(T.box, comp.mod.mangle('module'))
  module[rename].linkage = 'available_externally'  # make sure we know it's visible here

  module[rename].mod = comp.mod
  module.imports.add(file)


@A.link_node.method
def emit(self, module):
  base, name = os.path.split(module.file)
  file = M.find_file(self.name, paths=[base])
  if not file:
    Q.abort("Can't find link {!r}", self.name, pos=self.coords)
  module.links.add(file)


@A.lib_node.method
def emit(self, module):
  module.libs.add(self.name)


@A.macro_node.method
def emit(self, module):
  pass


@A.macro_node.method
def define(self, module, name):
  typ = T.vfunc(T.arg, *[T.arg for x in self.params])

  A.func_node(self.params, self.body, 'macro.func.real:' + name).emit(module)
  real_func = module.find_func(typ, 'macro.func.real:' + name)

  main_func = module.add_func(typ, name='macro.func.main:' + name)
  main_func.attributes.personality = module.runtime.personality
  main_func.args[0].add_attribute('sret')
  with module.add_func_body(main_func):
    with module.add_catch():
      module.call(real_func, *main_func.args)
      module.catch(module.builder.block)

    module.builder.ret_void()


@A.pass_node.method
def emit(self, module):
  pass


@A.return_node.method
def emit_local(self, module):
  if module.is_global:
    Q.warn('wtf')

  if self.value:
    module.store(module.emit(self.value), module.ret_ptr)

  module.builder.ret_void()


@A.save_node.method
def emit_local(self, module):
  if self.name:
    module[self.name] = module.ret_ptr

  module.store(module.emit(self.value), module.ret_ptr)


# Block statements ############################################################


@A.if_node.method
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


@A.with_node.method
def emit(self, module):
  user_box = module.emit(self.expr)
  user_ptr = module.get_value(user_box, typ=T.vfunc(T.arg, T.arg))
  module.check_callable(user_box, 1)

  func_box = module.emit(A.func_node(self.params, self.body))

  ptrs = module.fnalloc(T.null, func_box)

  env = module.get_env(user_box)
  has_env = module.builder.icmp_unsigned('!=', env, T.arg(None))
  with module.builder.if_then(has_env):
    env_box = module.load(env)
    module.store(env_box, ptrs[0])

  module.call(user_ptr, *ptrs)


@A.loop_node.method
def emit(self, module):
  with module.add_loop():
    with module.goto(module.before):
      module.builder.branch(module.loop)

    with module.goto(module.loop):
      module.emit(self.body)
      if not module.builder.block.is_terminated:
        module.builder.branch(module.loop)


@A.until_node.method
def emit(self, module):
  with module.add_loop():
    with module.goto(module.before):
      module.builder.cbranch(module.truthy(self.pred), module.after, module.loop)

    with module.goto(module.loop):
      module.emit(self.body)
      if not module.builder.block.is_terminated:
        module.builder.branch(module.before)


@A.while_node.method
def emit(self, module):
  with module.add_loop():
    with module.goto(module.before):
      module.builder.cbranch(module.truthy(self.pred), module.loop, module.after)

    with module.goto(module.loop):
      module.emit(self.body)
      if not module.builder.block.is_terminated:
        module.builder.branch(module.before)


@A.for_node.method
def emit(self, module):
  # evaluate the expressions and pull out the function pointers
  func_box = module.emit(self.func)
  module.check_callable(func_box, 0)

  func_ptr = module.get_value(func_box, T.vfunc(T.arg))
  func_env = module.get_env(func_box)
  has_env = module.builder.icmp_unsigned('!=', func_env, T.arg(None))

  # set up the return pointers
  with module.goto_entry():
    ret_ptr = module.alloc(T.null)
    if isinstance(self.name, A.name_node):
      module[self.name.value] = ret_ptr
    elif isinstance(self.name, list):
      for name in flatten(self.name):
        module[name.value] = module.alloc(T.null)

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
      if not module.builder.block.is_terminated:
        module.builder.branch(module.before)


@A.catch_node.method
def emit(self, module):
  # create a pointer to save the return value of the whole node
  with module.goto_entry():
    ret_ptr = module.alloc(T.null, name='exc_var')

  # add a new block after our body executes
  end = module.builder.append_basic_block('end_catch')

  # make a note of the call stack depth
  trace_depth_val = module.load(module.trace_depth)

  with module.add_catch():
    # perform normal execution
    module.emit(self.body)

    # in case of a panic, save its value into the return pointer
    # and recover control at #end
    module.catch(end, into=ret_ptr)

  # no panics - everything went according to plan, so branch to #end
  module.builder.branch(end)

  # move to #end
  module.builder.position_at_end(end)

  # restore call stack depth
  module.store(trace_depth_val, module.trace_depth)

  return module.load(ret_ptr)


# Simple expressions ##########################################################

@A.name_node.method
def emit(self, module):
  if self.value not in module:
    Q.abort("Unknown name {!r}", self.value, pos=self.coords)

  if module.is_global:
    return module.load_global(self.value)

  else:
    return module.load(module[self.value])


@A.null_node.method
def emit(self, module):
  return T.null


@A.int_node.method
def emit(self, module):
  return T._int(self.value, module.get_vt('int'))


@A.float_node.method
def emit(self, module):
  return T._float(self.value, module.get_vt('float'))


@A.bool_node.method
def emit(self, module):
  return T._bool(self.value, module.get_vt('bool'))


@A.str_node.method
def emit(self, module):
  typ = T.arr(T.i8, len(self.value) + 1)
  ptr = module.add_global(typ, name=module.uniq('string'))
  ptr.initializer = typ(bytearray(self.value + '\0', 'utf-8'))
  gep = ptr.gep([T.i32(0), T.i32(0)])

  return T._str(gep, len(self.value), module.get_vt('str'))


@A.table_node.method
def emit_global(self, module):
  return module.static.new_table(module.uniq('table_lit'))


@A.table_node.method
def emit_local(self, module):
  ptr = module.runtime.new_table()
  return module.load(ptr)


@A.array_node.method
def emit_global(self, module):
  table_box = module.static.new_table(module.uniq('array'))

  for i, item in enumerate(self.items):
    key_node = A.int_node(i)
    val = module.emit(item)

    module.static.put(table_box, key_node, val)

  old_box = table_box
  table_box = T.insertvalue(table_box, module.get_vt('array'), T.ENV)
  module.static.repair(table_box, old_box)

  return table_box


@A.array_node.method
def emit_local(self, module):
  ptr = module.runtime.new_table()
  for i, item in enumerate(self.items):
    args = module.fnalloc(A.int_node(i).emit(module), module.emit(item))
    module.runtime.put(ptr, *args)

  ret = module.load(ptr)
  ret = module.insert(ret, module.get_vt('array'), T.ENV)

  return ret


@A.dict_node.method
def emit_global(self, module):
  table_box = module.static.new_table(module.uniq('array'))

  for key, item in self.items:
    key_node = key
    val = module.emit(item)

    module.static.put(table_box, key_node, val)

  if self.set_meta:
    old_box = table_box
    table_box = T.insertvalue(table_box, module.get_vt('dict'), T.ENV)
    module.static.repair(table_box, old_box)

  return table_box


@A.dict_node.method
def emit_local(self, module):
  ptr = module.runtime.new_table()

  for key, item in self.items:
    args = module.fnalloc(module.emit(key), module.emit(item))
    module.runtime.put(ptr, *args)

  ret = module.load(ptr)

  if self.set_meta:
    ret = module.insert(ret, module.get_vt('dict'), T.ENV)

  return ret


@A.func_node.method
def emit(self, module):
  typ = T.vfunc(T.arg, *[T.arg for x in self.params])

  func = module.add_func(typ, name=self.rename)
  func.attributes.personality = module.runtime.personality
  func.args[0].add_attribute('sret')

  bindings = set()

  with module:
    with module.add_func_body(func):
      for name, ptr in zip(self.params, func.args[1:]):
        module[name] = ptr

      module.emit(self.body)

      bindings = module.bindings

      if not module.builder.block.is_terminated:
        module.builder.ret_void()

  func_box = T._func(func, len(self.params))

  if bindings:
    env_ptr = module.runtime.new_table()

    func_box = module.insert(func_box, env_ptr, T.ENV)

    with module.goto_entry():
      key_ptr = module.alloc()
      self_ptr = module.alloc()

    module.store(func_box, self_ptr)

    for i, name in enumerate(bindings):
      module.store(A.str_node(name).emit(module), key_ptr)

      # cheesy hack - the only time any of these values will ever
      # have a bound value of False will be when it's the item
      # currently being bound, ie, it's this function
      if getattr(module[name], 'bound', None) is False:
        module.runtime.put(env_ptr, key_ptr, self_ptr)
      else:
        module.runtime.put(env_ptr, key_ptr, module[name])

  return func_box


@A.foreign_node.method
def emit(self, module):
  typ = T.vfunc(*[T.arg for param in self.params])
  func = module.find_func(typ, name=self.name)
  return T._func(func, len(self.params))


# Compound expressions ########################################################

@A.call_node.method
def emit_glboal(self, module):
  Q.abort("Can't call functions at global scope", pos=self.coords)


@A.call_node.method
def emit_local(self, module):
  func_box = module.emit(self.func)
  arg_boxes = [module.emit(arg) for arg in self.args]

  with module.trace(self.coords):
    return module.box_call(func_box, arg_boxes, catch=self.catch)


@A.meth_node.method
def emit_global(self, module):
  Q.abort("Can't call methods at global scope", pos=self.coords)


@A.meth_node.method
def emit_local(self, module):
  table = module.emit(self.lhs)
  key = module.emit(self.rhs)

  ret_ptr, *args = module.fnalloc(T.null, table, key)
  module.runtime.get(ret_ptr, *args)

  func_box = module.load(ret_ptr)
  arg_boxes = [table] + [module.emit(arg) for arg in self.args]

  with module.trace(self.coords):
    return module.box_call(func_box, arg_boxes, catch=self.catch)


@A.idx_node.method
def emit_global(self, module):
  # check if LHS is a module
  table_box = module.emit(self.lhs)
  if getattr(table_box, 'mod', None):
    return table_box.mod.load_global(self.rhs)

  # otherwise, do normal lookups
  else:
    return module.static.get(table_box, self.rhs)


@A.idx_node.method
def emit_local(self, module):
  table = module.emit(self.lhs)
  key = module.emit(self.rhs)

  ret_ptr, *args = module.fnalloc(T.null, table, key)
  module.runtime.get(ret_ptr, *args)
  return module.load(ret_ptr)


# Operator expressions ########################################################

@A.unary_node.method
def emit_global(self, module):
  Q.abort("Can't use unary operators at global scope", pos=self.coords)


@A.unary_node.method
def emit_local(self, module):
  arith = {
    '-': module.runtime.neg,
    '!': module.runtime.lnot,
  }

  val = module.emit(self.val)

  ret_ptr, arg = module.fnalloc(T.null, val)

  with module.trace(self.coords):
    arith[self.op](ret_ptr, arg)

  return module.load(ret_ptr)


@A.binary_node.method
def emit_global(self, module):
  if self.op == '::':
    lhs = module.emit(self.lhs)
    rhs = module.emit(self.rhs)

    ptr = module.add_global(T.box)
    ptr.initializer = rhs

    new_lhs = T.insertvalue(lhs, ptr, T.ENV)
    module.static.repair(new_lhs, lhs)

    return new_lhs

  else:
    Q.abort("Can't use binary operators at global scope", pos=self.coords)


@A.binary_node.method
def emit_local(self, module):
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

  if self.op == '::':
    lhs = module.emit(self.lhs)
    rhs = module.emit(self.rhs)

    ptr = module.runtime.box_malloc()
    module.store(rhs, ptr)
    return module.insert(lhs, ptr, T.ENV)

  elif self.op in ('|', '&'):
    with module.goto_entry():
      res = module.alloc(T.null)

    lhs = module.emit(self.lhs)
    module.store(lhs, res)

    t = module.truthy_val(lhs)
    if self.op == '|':
      t = module.builder.not_(t)

    with module.builder.if_then(t):
      rhs = module.emit(self.rhs)
      module.store(rhs, res)

    return module.load(res)

  elif self.op in arith:
    lhs = module.emit(self.lhs)
    rhs = module.emit(self.rhs)

    ret_ptr, *args = module.fnalloc(T.null, lhs, rhs)

    with module.trace(self.coords):
      arith[self.op](ret_ptr, *args)

    return module.load(ret_ptr)

  else:
    Q.abort("Invalid binary operator {!r}", self.op, pos=self.coords)


# Warning statements ##########################################################

@A.error_node.method
def emit(self, module):
  Q.abort(self.msg)


@A.warning_node.method
def emit(self, module):
  Q.warn(self.msg)


@A.hint_node.method
def emit(self, module):
  Q.hint(self.msg)
