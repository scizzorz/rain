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
  module.exports.initializer = static_table_alloc(module, name=module.mangle('exports.table'))

  imports = []
  links = []
  libs = []
  for stmt in self.stmts:
    ret = module.emit(stmt)
    if isinstance(stmt, import_node):
      imports.append(ret)
    elif isinstance(stmt, link_node):
      links.append(ret)
    elif isinstance(stmt, lib_node):
      libs.append(ret)

  return imports, links, libs


@program_node.method
def emit_main(self, module, mods=[]):
  with module.add_main():
    ret_ptr = module.alloc(T.box, T.null, name='ret_ptr')

    with module.add_abort() as abort:
      module.excall('rain_init_args', *module.main.args)

      for tmp in mods:
        if 'init' in tmp:
          with tmp.borrow_builder(module):
            init_box = load_global(tmp, 'init')
            init_ptr = module.get_value(init_box, typ=T.vfunc(T.arg))
            module.check_callable(init_box, 0, unwind=module.catch)
            module.fncall(init_ptr, T.null, unwind=module.catch)

      module.excall('rain_main', ret_ptr, module['main'], unwind=module.catch)

      abort(module.builder.block)

      ret_code = module.excall('rain_box_to_exit', ret_ptr)
      module.builder.ret(ret_code)


@block_node.method
def emit(self, module):
  for stmt in self.stmts:
    module.emit(stmt)

  if self.expr:
    return module.emit(self.expr)

  return T.null


# Helpers #####################################################################

# Put a value into a static table
def static_table_put(module, table_ptr, column_ptr, key_node, key, val):
  table = table_ptr.initializer

  # we can only hash things that are known to this compiler (not addresses)
  if not isinstance(key_node, literal_node):
    Q.abort('Unable to hash {!s}', key_node)

  # get these for storing
  column = T.column([key, val, None])
  column.next = None  # for later!
  column.key = key_node

  # compute the hash and allocate a new column for it
  idx = key_node.hash() % T.HASH_SIZE
  column_ptr.initializer = column

  # update the table array and then update the initializer
  if not isinstance(table.constant[idx], ir.GlobalVariable):
    # no chain
    table.constant[idx] = column_ptr
    table_ptr.initializer = table.type(table.constant)

  else:
    # chain through the list until we find the right key node or the end of the list
    chain = table.constant[idx]
    while chain.initializer.next is not None and chain.initializer.key != key_node:
      chain = chain.initializer.next

    if chain.initializer.key == key_node:  # we found the same key node in the list
      save = chain.initializer.next
      chain.initializer.constant[1] = val

      chain.initializer = chain.initializer.type(chain.initializer.constant)
      chain.initializer.next = save
      chain.initializer.key = key_node

    else:  # we never found the same key node, but we did find the end of the list
      save = chain.initializer.key
      chain.initializer.constant[2] = column_ptr

      chain.initializer = chain.initializer.type(chain.initializer.constant)
      chain.initializer.next = column_ptr
      chain.initializer.key = save


# Get a value from a static table
def static_table_get(module, table_ptr, key_node, key):
  table = table_ptr.initializer

  idx = key_node.hash() % T.HASH_SIZE
  chain = table.constant[idx]

  if not isinstance(chain, ir.GlobalVariable):
    return T.null

  while chain.initializer.next is not None and chain.initializer.key != key_node:
    chain = chain.initializer.next

  if chain.initializer.key == key_node:
    return chain.initializer.constant[1]

  return T.null


# Allocate a [column] array
def static_table_alloc(module, name):
  # make an empty array of column*
  typ = T.arr(T.ptr(T.column), T.HASH_SIZE)
  ptr = module.add_global(typ, name=name)
  ptr.initializer = typ([None] * T.HASH_SIZE)
  return static_table_from_ptr(module, ptr)


# Return a box from a [column] array
def static_table_from_ptr(module, ptr):
  gep = ptr.gep([T.i32(0), T.i32(0)])

  box = T._table(gep)
  box.source = ptr  # save this for later!

  return box


# Put a value into the exports table
def export_global(module, name: str, value: "LLVM value"):
  key_node = str_node(name)
  key = key_node.emit(module)
  column_ptr = module.find_global(T.column, name=module.mangle(name + '.export'))
  static_table_put(module, module.exports.initializer.source, column_ptr, key_node, key, value)
  return column_ptr.gep([T.i32(0), T.i32(1)])


# Store a value into a global (respecting whether it's exported or not)
def store_global(module, name: str, value: "LLVM value"):
  if isinstance(module[name], ir.GlobalVariable):
    module[name].initializer = value
  else:
    module[name] = export_global(module, name, value)
    module[name].col = value


# Load a value from a global (respecting whether it's exported or not)
def load_global(module, name: str):
  if isinstance(module[name], ir.GlobalVariable):
    return module[name].initializer
  else:
    return module[name].col


# Simple statements ###########################################################

@assn_node.method
def emit(self, module):
  if isinstance(self.lhs, name_node):
    if module.is_global:
      if self.export:
        column_ptr = module.find_global(T.column, name=module.mangle(self.lhs.value + '.export'))
        module[self.lhs.value] = column_ptr.gep([T.i32(0), T.i32(1)])

        val = module.emit(self.rhs)
        store_global(module, self.lhs.value, val)
        return

      if self.let:
        module[self.lhs] = module.add_global(T.box, name=module.mangle(self.lhs.value))

      if self.lhs not in module:
        Q.abort("Undeclared global {!r}", self.lhs.value)

      store_global(module, self.lhs.value, module.emit(self.rhs))
      return

    if self.let:
      with module.goto_entry():
        module[self.lhs] = module.alloc(T.box)
        module[self.lhs].bound = False  # cheesy hack - see @func_node

    rhs = module.emit(self.rhs)

    if self.lhs not in module:
      Q.abort("Undeclared name {!r}", self.lhs.value)

    module[self.lhs].bound = True
    module.store(rhs, module[self.lhs])

  elif isinstance(self.lhs, idx_node):
    if module.is_global:
      table_ptr = module.emit(self.lhs.lhs).source
      key_node = self.lhs.rhs
      key = module.emit(key_node)
      val = module.emit(self.rhs)

      column_ptr = module.add_global(T.column, name=module.uniq('column'))
      static_table_put(module, table_ptr, column_ptr, key_node, key, val)
      return

    table = module.emit(self.lhs.lhs)
    key = module.emit(self.lhs.rhs)
    val = module.emit(self.rhs)

    module.exfncall('rain_put', table, key, val)


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
    Q.abort("Can't export value {!r} as foreign at non-global scope", self.name)

  if self.name not in module:
    Q.abort("Can't export unknown value {!r}", self.name)

  glob = module.add_global(T.ptr(T.box), name=self.rename)
  glob.initializer = module[self.name]


@import_node.method
def emit(self, module):
  if module.is_local:
    Q.abort("Can't import module {!r} at non-global scope", self.name)

  # add the module's directory to the lookup path
  if getattr(module, 'file', None):
    base, name = os.path.split(module.file)
    file = M.find_rain(self.name, paths=[base])
  else:
    file = M.find_rain(self.name)

  if not file:
    Q.abort("Can't find module {!r}", self.name)

  comp = C.get_compiler(file)
  comp.goodies()

  module.import_from(comp.mod)
  glob = module.get_global(comp.mod.mangle('exports.table'))

  rename = self.rename or comp.mname

  module[rename] = module.add_global(T.box, module.mangle(rename))
  module[rename].initializer = static_table_from_ptr(module, glob)
  module[rename].mod = comp.mod
  return file


@link_node.method
def emit(self, module):
  if module.is_local:
    Q.abort("Can't link file {!r} at non-global scope", self.name)

  base, name = os.path.split(module.file)
  file = M.find_file(self.name, paths=[base])
  return file


@macro_node.method
def emit(self, module):
  pass


@macro_node.method
def expand(self, module):
  typ = T.vfunc(T.arg, *[T.arg for x in self.params])

  func_node(self.params, self.body).emit(module, name='macro.func.real')
  real_func = module.find_func(typ, 'macro.func.real')

  main_func = module.add_func(typ, name='macro.func.main')
  main_func.attributes.personality = module.extern('rain_personality_v0')
  main_func.args[0].add_attribute('sret')
  with module.add_func_body(main_func):
    with module.add_abort() as abort:
      module.call(real_func, *main_func.args, unwind=module.catch)
      abort(module.builder.block)

    module.builder.ret_void()


@lib_node.method
def emit(self, module):
  if module.is_local:
    Q.abort("Can't link library {!r} at non-global scope", self.name)

  return self.name


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

  env = module.get_env(func_box)
  is_env = module.builder.icmp_unsigned('!=', env, T.arg(None))
  with module.builder.if_then(is_env):
    module.store(func_box, ptrs[0])

  module.call(user_ptr, *ptrs)


@loop_node.method
def emit(self, module):
  with module.add_loop() as (before, loop):
    with before:
      module.builder.branch(module.loop)

    with loop:
      module.emit(self.body)
      module.builder.branch(module.loop)


@until_node.method
def emit(self, module):
  with module.add_loop() as (before, loop):
    with before:
      module.builder.cbranch(module.truthy(self.pred), module.after, module.loop)

    with loop:
      module.emit(self.body)
      module.builder.branch(module.before)


@while_node.method
def emit(self, module):
  with module.add_loop() as (before, loop):
    with before:
      module.builder.cbranch(module.truthy(self.pred), module.loop, module.after)

    with loop:
      module.emit(self.body)
      module.builder.branch(module.before)


@for_node.method
def emit(self, module):
  # evaluate the expression and pull out the function pointer
  func_box = module.emit(self.func)
  func_ptr = module.get_value(func_box, T.vfunc(T.arg))
  module.check_callable(func_box, 0)

  env = module.get_env(func_box)
  is_env = module.builder.icmp_unsigned('!=', env, T.arg(None))

  # set up the return pointer
  with module.goto_entry():
    ret_ptr = module[self.name] = module.alloc(T.box, name='for_var')

  with module.add_loop() as (before, loop):
    with before:
      # call our function and break if it returns null
      module.store(T.null, ret_ptr)
      with module.builder.if_then(is_env):
        module.store(func_box, ret_ptr)

      module.call(func_ptr, ret_ptr)
      box = module.load(ret_ptr)
      typ = module.get_type(box)
      not_null = module.builder.icmp_unsigned('!=', typ, T.ityp.null)
      module.builder.cbranch(not_null, module.loop, module.after)

    with loop:
      module.emit(self.body)
      module.builder.branch(module.before)


@catch_node.method
def emit(self, module):
  with module.goto_entry():
    ret_ptr = module[self.name] = module.alloc(T.box, T.null, name='exc_var')

  end = module.builder.append_basic_block('end_catch')

  with module.add_catch(True) as catch:
    module.emit(self.body)
    catch(ret_ptr, end)

  module.builder.branch(end)
  module.builder.position_at_end(end)


# Simple expressions ##########################################################

@name_node.method
def emit(self, module):
  if self.value not in module:
    Q.abort("Unknown name {!r}", self.value)

  if module.is_global:
    return load_global(module, self.value)

  return module.load(module[self.value])


@null_node.method
def emit(self, module):
  return T.null


@int_node.method
def emit(self, module):
  return T._int(self.value)


@float_node.method
def emit(self, module):
  return T._float(self.value)


@bool_node.method
def emit(self, module):
  return T._bool(self.value)


@str_node.method
def emit(self, module):
  typ = T.arr(T.i8, len(self.value) + 1)
  ptr = module.add_global(typ, name=module.uniq('string'))
  ptr.initializer = typ(bytearray(self.value + '\0', 'utf-8'))
  gep = ptr.gep([T.i32(0), T.i32(0)])

  return T._str(gep, len(self.value))


@table_node.method
def emit(self, module):
  if module.is_global:
    return static_table_alloc(module, module.uniq('table'))

  ptr = module.excall('rain_new_table')
  return module.load(ptr)


@array_node.method
def emit(self, module):
  if module.is_global:
    table_box = static_table_alloc(module, module.uniq('array'))
    table_ptr = table_box.source

    for i, item in enumerate(self.items):
      key_node = int_node(i)
      key = module.emit(key_node)
      val = module.emit(item)

      column_ptr = module.add_global(T.column, name=module.uniq('column'))
      static_table_put(module, table_ptr, column_ptr, key_node, key, val)

    if 'base.array.exports' in module.llvm.globals:
      table_box = T.insertvalue(table_box, module.get_global('base.array.exports'), T.ENV)
      table_box.source = table_ptr

    return table_box

  ptr = module.excall('rain_new_table')
  for i, item in enumerate(self.items):
    args = module.fnalloc(int_node(i).emit(module), module.emit(item))
    module.excall('rain_put', ptr, *args)

  ret = module.load(ptr)
  if 'base.array.exports' in module.llvm.globals:
    ret = module.insert(ret, module.get_global('base.array.exports'), T.ENV)

  return ret


@func_node.method
def emit(self, module, name=None):
  env = OrderedDict()
  for scope in module.scopes[1:]:
    for nm, ptr in scope.items():
      env[nm] = ptr

  env_typ = T.arr(T.box, len(env))
  typ = T.vfunc(T.arg, *[T.arg for x in self.params])

  func = module.add_func(typ, name=name)
  func.attributes.personality = module.extern('rain_personality_v0')
  func.args[0].add_attribute('sret')

  with module:
    with module.add_func_body(func):
      if env:
        env_box = module.load(func.args[0])

        env_ptr = module.get_env(env_box)

        for i, (name, ptr) in enumerate(env.items()):
          module.store(str_node(name).emit(module), func.args[0])
          module[name] = module.excall('rain_get_ptr', env_ptr, func.args[0])

        module.store(T.null, func.args[0])

      for name, ptr in zip(self.params, func.args[1:]):
        module[name] = ptr

      module.emit(self.body)

      if not module.builder.block.is_terminated:
        module.builder.ret_void()

  func_box = T._func(func, len(self.params))

  if env:
    env_ptr = module.excall('rain_new_table')

    func_box = module.insert(func_box, env_ptr, T.ENV)

    with module.goto_entry():
      key_ptr = module.alloc(T.box)
      self_ptr = module.alloc(T.box)

    module.store(func_box, self_ptr)

    for i, (name, ptr) in enumerate(env.items()):
      # cheesy hack - the only time any of these values will ever
      # have a bound value of False will be when it's the item
      # currently being bound, ie, it's this function
      module.store(str_node(name).emit(module), key_ptr)
      if getattr(ptr, 'bound', None) is False:
        module.excall('rain_put', env_ptr, key_ptr, self_ptr)
      else:
        module.excall('rain_put', env_ptr, key_ptr, ptr)

  return func_box


@foreign_node.method
def emit(self, module):
  typ = T.vfunc(*[T.arg for param in self.params])
  func = module.find_func(typ, name=self.name)
  return T._func(func, len(self.params))


# Compound expressions ########################################################

def get_exception(module, name):
  glob = module.find_global(T.ptr(T.box), name)
  return module.load(glob)


def do_call(module, func_box, arg_boxes, catch=False):
  func_ptr = module.get_value(func_box, typ=T.vfunc(T.arg, *[T.arg] * len(arg_boxes)))

  module.check_callable(func_box, len(arg_boxes))
  ptrs = module.fnalloc(T.null, *arg_boxes)

  env = module.get_env(func_box)
  is_env = module.builder.icmp_unsigned('!=', env, T.arg(None))
  with module.builder.if_then(is_env):
    module.store(func_box, ptrs[0])

  if catch:
    with module.add_catch() as catch:
      module.call(func_ptr, *ptrs, unwind=module.catch)

      catch(ptrs[0], module.builder.block)

      return module.load(ptrs[0])

  module.call(func_ptr, *ptrs)
  return module.load(ptrs[0])


@call_node.method
def emit(self, module):
  if module.is_global:
    Q.abort("Can't call functions at global scope")

  func_box = module.emit(self.func)
  arg_boxes = [module.emit(arg) for arg in self.args]

  return do_call(module, func_box, arg_boxes, catch=self.catch)


@meth_node.method
def emit(self, module):
  if module.is_global:
    Q.abort("Can't call methods at global scope")

  table = module.emit(self.lhs)
  key = module.emit(self.rhs)

  ret_ptr = module.exfncall('rain_get', T.null, table, key)

  func_box = module.load(ret_ptr)
  arg_boxes = [table] + [module.emit(arg) for arg in self.args]

  return do_call(module, func_box, arg_boxes, catch=self.catch)


@idx_node.method
def emit(self, module):
  if module.is_global:
    # check if LHS is a module
    if getattr(module[self.lhs], 'mod', None):
      return load_global(module[self.lhs].mod, self.rhs)

    # otherwise, do normal lookups
    table_ptr = module.emit(self.lhs).source
    key_node = self.rhs
    key = module.emit(key_node)

    return static_table_get(module, table_ptr, key_node, key)

  table = module.emit(self.lhs)
  key = module.emit(self.rhs)

  ret_ptr = module.exfncall('rain_get', T.null, table, key)
  return module.load(ret_ptr)


# Operator expressions ########################################################

@unary_node.method
def emit(self, module):
  if module.is_global:
    Q.abort("Can't use unary operators at global scope")

  arith = {
    '-': 'rain_neg',
    '!': 'rain_not',
  }

  val = module.emit(self.val)

  ret_ptr = module.exfncall(arith[self.op], T.null, val)
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

      if getattr(lhs, 'source', None): # this is for my dirty table hack
        new_lhs.source = lhs.source

      return new_lhs

    ptr = module.excall('rain_box_malloc')
    module.store(rhs, ptr)
    return module.insert(lhs, ptr, T.ENV)

  if module.is_global:
    Q.abort("Can't use binary operators at global scope")

  if self.op in ('|', '&'):
    with module.goto_entry():
      res = module.alloc(T.box)

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
    '+': 'rain_add',
    '-': 'rain_sub',
    '*': 'rain_mul',
    '/': 'rain_div',
    '==': 'rain_eq',
    '!=': 'rain_ne',
    '>': 'rain_gt',
    '>=': 'rain_ge',
    '<': 'rain_lt',
    '<=': 'rain_le',
    '$': 'rain_string_concat',
  }

  if self.op not in arith:
    Q.abort("Invalid binary operator {!r}", self.op)

  lhs = module.emit(self.lhs)
  rhs = module.emit(self.rhs)

  ret_ptr = module.exfncall(arith[self.op], T.null, lhs, rhs)
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
