from . import compiler as C
from . import module as M
from . import types as T
from .ast import *
from collections import OrderedDict
from llvmlite import ir
import os.path


# Program structure ###########################################################

@program_node.method
def emit(self, module):
  module.metatable_key = module.add_global(T.box)
  module.metatable_key.initializer = str_node('metatable').emit(module)

  module.exports = module.add_global(T.box, name=module.mangle('exports'))
  module.exports.initializer = static_table_alloc(module, name=module.mangle('exports.table'))

  imports = []
  links = []
  for stmt in self.stmts:
    ret = module.emit(stmt)
    if isinstance(stmt, import_node):
      imports.append(ret)
    elif isinstance(stmt, link_node):
      links.append(ret)

  return imports, links


@program_node.method
def emit_main(self, module):
  with module.add_main():
    ret_ptr = module.alloc(T.box, T.null, name='ret_ptr')

    with module.add_abort() as abort:
      module.excall('rain_main', ret_ptr, module['main'], *module.main.args, unwind=module.catch)

      abort(module.builder.block)

      ret_code = module.excall('rain_box_to_exit', ret_ptr)
      module.builder.ret(ret_code)


@block_node.method
def emit(self, module):
  for stmt in self.stmts:
    module.emit(stmt)


# Helpers #####################################################################

# Put a value into a static table
def static_table_put(module, table_ptr, column_ptr, key_node, key, val):
  table = table_ptr.initializer

  # we can only hash things that are known to this compiler (not addresses)
  if not isinstance(key_node, literal_node):
    module.panic('Unable to hash {!s}', key_node)

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
def static_table_alloc(module, name, metatable=None):
  # make an empty array of column*
  typ = T.arr(T.ptr(T.column), T.HASH_SIZE)
  ptr = module.add_global(typ, name=name)
  ptr.initializer = typ([None] * T.HASH_SIZE)
  return static_table_from_ptr(module, ptr, metatable)


# Return a box from a [column] array
# Inject the metatable if necessary
def static_table_from_ptr(module, ptr, metatable=None):
  gep = ptr.gep([T.i32(0), T.i32(0)])

  box = T._table(gep)
  box.source = ptr  # save this for later!

  if metatable:
    # get these for storing
    mt_val = module.emit(metatable)
    mt_key = module.metatable_key.initializer
    mt_column = T.column([mt_key, mt_val, T.ptr(T.column)(None)])

    # compute hash and allocate a column for it
    mt_idx = str_node('metatable').hash() % T.HASH_SIZE
    column_ptr = module.add_global(T.column, name=module.uniq('column'))
    column_ptr.initializer = mt_column

    ptr.initializer.constant[mt_idx] = column_ptr
    ptr.initializer = ptr.initializer.type(ptr.initializer.constant)

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
        module.panic("Undeclared global {!r}", self.lhs.value)

      store_global(module, self.lhs.value, module.emit(self.rhs))
      return

    if self.let:
      with module.goto_entry():
        module[self.lhs] = module.alloc(T.box)
        module[self.lhs].bound = False  # cheesy hack - see @func_node

    rhs = module.emit(self.rhs)

    if self.lhs not in module:
      module.panic("Undeclared name {!r}", self.lhs.value)

    module[self.lhs].bound = True
    module.store(rhs, module[self.lhs])

  elif isinstance(self.lhs, idx_node):
    if module.is_global:
      table_ptr = load_global(module, self.lhs.lhs).source
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
    module.panic("Can't export value {!r} as foreign at non-global scope", self.name)

  if self.name not in module:
    module.panic("Can't export unknown value {!r}", self.name)

  glob = module.add_global(T.ptr(T.box), name=self.rename)
  glob.initializer = module[self.name]


@import_node.method
def emit(self, module):
  if module.is_local:
    module.panic("Can't import module {!r} at non-global scope", self.name)

  # add the module's directory to the lookup path
  base, name = os.path.split(module.file)
  file = M.find_rain(self.name, paths=[base])
  if not file:
    module.panic("Can't find module {!r}", self.name)

  comp = C.get_compiler(file)
  comp.goodies()

  module.import_from(comp.mod)
  glob = module.get_global(comp.mod.mangle('exports.table'))

  rename = self.rename or comp.mod.mname

  module[rename] = module.add_global(T.box, module.mangle(rename))
  module[rename].initializer = static_table_from_ptr(module, glob)
  module[rename].mod = comp.mod
  return file


@link_node.method
def emit(self, module):
  if module.is_local:
    module.panic("Can't link file {!r} at non-global scope", self.name)

  base, name = os.path.split(module.file)
  file = M.find_file(self.name, paths=[base])
  return file


@macro_node.method
def emit(self, module):
  pass


@macro_node.method
def expand(self, module):
  func_node(self.params, self.body).emit(module)


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
  check_callable(module, user_box, 1)

  func_box = module.emit(func_node(self.params, self.body))

  module.fncall(user_ptr, T.null, func_box)


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
  check_callable(module, func_box, 0)

  # set up the return pointer
  with module.goto_entry():
    ret_ptr = module[self.name] = module.alloc(T.box, name='for_var')

  with module.add_loop() as (before, loop):
    with before:
      # call our function and break if it returns null
      module.store(T.null, ret_ptr)
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
    module.panic("Unknown name {!r}", self.value)

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
    return static_table_alloc(module, module.uniq('table'), metatable=self.metatable)

  ptr = module.excall('rain_new_table')

  if self.metatable:
    val = module.emit(self.metatable)

    with module.goto_entry():
      val_ptr = module.alloc(T.box, name='key_ptr')

    module.store(val, val_ptr)
    module.excall('rain_put', ptr, module.metatable_key, val_ptr)

  return module.load(ptr)


@func_node.method
def emit(self, module):
  env = OrderedDict()
  for scope in module.scopes[1:]:
    for nm, ptr in scope.items():
      env[nm] = ptr

  if env:
    env_typ = T.arr(T.box, len(env))
    typ = T.vfunc(T.ptr(env_typ), T.arg, *[T.arg for x in self.params])

    func = module.add_func(typ)
    func.attributes.personality = module.extern('rain_personality_v0')
    func.args[0].add_attribute('nest')
    func.args[1].add_attribute('sret')

  else:
    typ = T.vfunc(T.arg, *[T.arg for x in self.params])

    func = module.add_func(typ)
    func.attributes.personality = module.extern('rain_personality_v0')
    func.args[0].add_attribute('sret')

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

      module.emit(self.body)

      if not module.builder.block.is_terminated:
        module.builder.ret_void()

  if env:
    env_raw_ptr = module.excall('GC_malloc', T.i32(T.BOX_SIZE * len(env)))
    env_ptr = module.builder.bitcast(env_raw_ptr, T.ptr(env_typ))

    func = module.add_tramp(func, env_ptr)
    func_i64 = module.builder.ptrtoint(func, T.i64)
    func_box = module.insert(T._func(args=len(self.params)), func_i64, 1)

    env_val = env_typ(None)

    for i, (name, ptr) in enumerate(env.items()):
      # cheesy hack - the only time any of these values will ever
      # have a bound value of False will be when it's the item
      # currently being bound, ie, it's this function
      if getattr(ptr, 'bound', None) is False:
        env_val = module.insert(env_val, func_box, i)
      else:
        env_val = module.insert(env_val, module.load(ptr), i)

    module.store(env_val, env_ptr)

    return func_box

  return T._func(func, len(self.params))


@foreign_node.method
def emit(self, module):
  typ = T.vfunc(*[T.arg for param in self.params])
  func = module.find_func(typ, name=self.name)
  return T._func(func, len(self.params))


# Compound expressions ########################################################

def get_exception(module, name):
  glob = module.find_global(T.ptr(T.box), name)
  return module.load(glob)


def check_callable(module, box, args):
  func_typ = module.get_type(box)
  is_func = module.builder.icmp_unsigned('!=', T.ityp.func, func_typ)
  with module.builder.if_then(is_func):
    module.excall('rain_throw', get_exception(module, 'rain_exc_uncallable'))

  exp_args = module.get_size(box)
  arg_match = module.builder.icmp_unsigned('!=', exp_args, T.i32(args))
  with module.builder.if_then(arg_match):
    module.excall('rain_throw', get_exception(module, 'rain_exc_arg_mismatch'))


def do_call(module, func_box, arg_boxes, catch=False):
  func_ptr = module.get_value(func_box, typ=T.vfunc(T.arg, *[T.arg] * len(arg_boxes)))

  check_callable(module, func_box, len(arg_boxes))

  if catch:
    with module.add_catch() as catch:
      ret_ptr = module.fncall(func_ptr, T.null, *arg_boxes, unwind=module.catch)

      catch(ret_ptr, module.builder.block)

      return module.load(ret_ptr)

  ret_ptr = module.fncall(func_ptr, T.null, *arg_boxes)
  return module.load(ret_ptr)


@call_node.method
def emit(self, module):
  if module.is_global:
    module.panic("Can't call functions at global scope")

  func_box = module.emit(self.func)
  arg_boxes = [module.emit(arg) for arg in self.args]

  return do_call(module, func_box, arg_boxes, catch=self.catch)


@meth_node.method
def emit(self, module):
  if module.is_global:
    module.panic("Can't call methods at global scope")

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
    table_ptr = module[self.lhs].col.source
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
    module.panic("Can't use unary operators at global scope")

  arith = {
    '-': 'rain_neg',
    '!': 'rain_not',
  }

  val = module.emit(self.val)

  ret_ptr = module.exfncall(arith[self.op], T.null, val)
  return module.load(ret_ptr)


@binary_node.method
def emit(self, module):
  if module.is_global:
    module.panic("Can't use binary operators at global scope")

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
    module.panic("Invalid binary operator {!r}".format(self.op))

  lhs = module.emit(self.lhs)
  rhs = module.emit(self.rhs)

  ret_ptr = module.exfncall(arith[self.op], T.null, lhs, rhs)
  return module.load(ret_ptr)


@is_node.method
def emit(self, module):
  if module.is_global:
    module.panic("Can't check types at global scope")

  lhs = module.emit(self.lhs)
  lhs_typ = module.get_type(lhs)
  res = module.builder.icmp_unsigned('==', getattr(T.ityp, self.typ), lhs_typ)
  res = module.builder.zext(res, T.i64)
  return module.insert(T._bool(False), res, 1)
