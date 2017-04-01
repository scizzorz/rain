from . import ast as A
from . import error as Q
from . import scope as S
from . import token as K
from . import types as T
from contextlib import contextmanager
from llvmlite import binding
from llvmlite import ir
from os.path import isdir, isfile
from os.path import join
import os.path
import re

name_chars = re.compile('[^a-z0-9]')


# get default paths
def get_paths():
  return ['.'] + os.getenv('RAINPATH', '').split(':') + [os.environ['RAINBASE'], os.environ['RAINLIB']]


# normalize a name - remove all special characters and cases
def normalize_name(name):
  return name_chars.sub('', name.lower())


# find a rain file from a module identifier
def find_rain(src, paths=[]):
  paths = paths + get_paths()

  for path in paths:
    if isfile(join(path, src) + '.rn'):
      return join(path, src) + '.rn'
    elif isfile(join(path, src)) and src.endswith('.rn'):
      return join(path, src)
    elif isdir(join(path, src)) and isfile(join(path, src, '_pkg.rn')):
      return join(path, src, '_pkg.rn')


# find any file from a string
def find_file(src, paths=[]):
  paths = paths + get_paths()

  for path in paths:
    if os.path.isfile(join(path, src)):
      return join(path, src)


# find a module name
def find_name(src):
  path = os.path.abspath(src)
  path, name = os.path.split(path)
  fname, ext = os.path.splitext(name)

  if fname == '_pkg':
    _, fname = os.path.split(path)

  mname = normalize_name(fname)

  proot = []
  while path and os.path.isfile(join(path, '_pkg.rn')):
    path, name = os.path.split(path)
    proot.insert(0, normalize_name(name))

  if not src.endswith('_pkg.rn'):
    proot.append(mname)

  qname = '.'.join(proot)

  return (qname, mname)


# partially apply a context manager
@contextmanager
def ctx_partial(func, *args, **kwargs):
  with func(*args, **kwargs) as val:
    yield val


externs = {
  'GC_malloc': T.func(T.ptr(T.i8), [T.i32]),

  'rain_abort': T.vfunc(),
  'rain_box_malloc': T.func(T.arg, []),
  'rain_box_to_exit': T.func(T.i32, [T.arg]),
  'rain_catch': T.vfunc(T.arg),
  'rain_check_callable': T.vfunc(T.arg, T.i32),
  'rain_init_gc': T.func(T.i32, []),
  'rain_init_args': T.vfunc(T.i32, T.ptr(T.ptr(T.i8))),
  'rain_main': T.vfunc(T.arg, T.arg),
  'rain_personality_v0': T.func(T.i32, [], var_arg=True),
  'rain_print': T.vfunc(T.arg),
  'rain_throw': T.vfunc(T.arg),

  'rain_neg': T.vfunc(T.arg, T.arg),
  'rain_not': T.vfunc(T.arg, T.arg),

  'rain_add': T.bin,
  'rain_sub': T.bin,
  'rain_mul': T.bin,
  'rain_div': T.bin,

  'rain_and': T.bin,
  'rain_or': T.bin,

  'rain_eq': T.bin,
  'rain_ne': T.bin,
  'rain_gt': T.bin,
  'rain_ge': T.bin,
  'rain_lt': T.bin,
  'rain_le': T.bin,

  'rain_string_concat': T.bin,

  'rain_new_table': T.func(T.arg, []),
  'rain_new_pair': T.vfunc(T.arg, T.arg),
  'rain_get_ptr': T.func(T.arg, [T.arg, T.arg]),
  'rain_put': T.bin,
  'rain_get': T.bin,
}


class Module(S.Scope):
  @staticmethod
  def dekey(key):
    if isinstance(key, (A.name_node, A.str_node)):
      key = key.value
    if isinstance(key, (K.name_token, K.string_token)):
      key = key.value
    return normalize_name(key)

  def __init__(self, file=None, name=None):
    S.Scope.__init__(self)

    if name:
      self.qname = self.mname = name
    else:
      self.file = file
      self.qname, self.mname = find_name(self.file)

    self.llvm = ir.Module(name=self.qname)
    self.llvm.triple = binding.get_default_triple()

    typ = T.arr(T.i8, len(self.qname) + 1)
    ptr = self.add_global(typ, name=self.mangle('_name'))
    ptr.initializer = typ(bytearray(self.qname + '\0', 'utf-8'))
    self.name_ptr = ptr.gep([T.i32(0), T.i32(0)])

    for name in externs:
      self.extern(name)

    self.builder = None
    self.arg_ptrs = None
    self.catch = None
    self.catchall = None
    self.before = None
    self.loop = None
    self.after = None
    self.ret_ptr = None
    self.callable_ptr = None

    self.name_counter = 0

  def __str__(self):
    return 'Module {!r}'.format(self.qname)

  def __repr__(self):
    return '<{!s}>'.format(self)

  def __getitem__(self, key):
    return super().__getitem__(self.dekey(key))

  def __setitem__(self, key, val):
    super().__setitem__(self.dekey(key), val)

  def __contains__(self, key):
    return super().__contains__(self.dekey(key))

  # wrapper to emit IR for a node
  def emit(self, node):
    return node.emit(self)

  @property
  def ir(self):
    return str(self.llvm)

  @property
  def is_global(self):
    return (not self.builder)

  @property
  def is_local(self):
    return bool(self.builder)

  # save and restore some module attributes around a code block
  @contextmanager
  def stack(self, *attrs):
    saved = [getattr(self, attr) for attr in attrs]
    yield
    for attr, val in zip(attrs, saved):
      setattr(self, attr, val)

  # mangle a name
  def mangle(self, name):
    return self.qname + '.' + name

  # generate a unique name
  def uniq(self, name):
    ret = self.mangle('{}.{}'.format(name, self.name_counter))
    self.name_counter += 1
    return ret

  # Global helpers ############################################################

  # main function
  @property
  def main(self):
    typ = T.func(T.i32, (T.i32, T.ptr(T.ptr(T.i8))))
    func = self.find_func(typ, name='main')
    func.attributes.personality = self.extern('rain_personality_v0')
    return func

  # add a new function
  def add_func(self, typ, name=None):
    if not name:
      name = self.uniq('func')
    return ir.Function(self.llvm, typ, name=name)

  # add or get an existing function
  def find_func(self, typ, name):
    if name in self.llvm.globals:
      return self.llvm.get_global(name)

    return self.add_func(typ, name=name)

  # add a new global
  def add_global(self, typ, name=None):
    if not name:
      name = self.uniq('glob')
    return ir.GlobalVariable(self.llvm, typ, name=name)

  def get_global(self, name):
    return self.llvm.get_global(name)

  # add or get an existing global
  def find_global(self, typ, name):
    if name in self.llvm.globals:
      return self.llvm.get_global(name)

    return self.add_global(typ, name=name)

  # add or find an external function
  def extern(self, name):
    return self.find_func(externs[name], name=name)

  # import globals from another module
  def import_llvm(self, other):
    for val in other.llvm.global_values:
      if val.name in self.llvm.globals:
        continue

      if isinstance(val, ir.Function):
        ir.Function(self.llvm, val.ftype, name=val.name)
      else:
        g = ir.GlobalVariable(self.llvm, val.type.pointee, name=val.name)
        g.linkage = 'available_externally'
        g.initializer = val.initializer

  # import the scope from other modules
  def import_scope(self, other):
    for name, val in other.globals.items():
      self[name] = val

  # Block helpers #############################################################

  @contextmanager
  def add_builder(self, block):
    with self.stack('builder'):
      self.builder = ir.IRBuilder(block)
      yield self.builder

  @contextmanager
  def borrow_builder(self, other):
    with self.stack('builder'):
      self.builder = other.builder
      yield self.builder

  @contextmanager
  def add_func_body(self, func):
    with self.stack('ret_ptr', 'callable_ptr', 'catchall', 'arg_ptrs'):
      entry = func.append_basic_block('entry')
      body = func.append_basic_block('body')
      self.ret_ptr = func.args[0]
      self.arg_ptrs = []
      self.catchall = False
      with self.add_builder(entry):
        self.callable_ptr = self.alloc(T.box)
        self.builder.branch(body)

      with self.add_builder(body):
        yield

  @contextmanager
  def add_main(self):
    with self.stack('callable_ptr', 'arg_ptrs'):
      self.arg_ptrs = []
      block = self.main.append_basic_block(name='entry')
      with self.add_builder(block):
        self.callable_ptr = self.alloc(T.box)
        yield self.main

  @contextmanager
  def add_loop(self):
    with self.stack('before', 'loop', 'after'):
      self.before = self.builder.append_basic_block('before')
      self.loop = self.builder.append_basic_block('loop')
      self.after = self.builder.append_basic_block('after')

      self.builder.branch(self.before)

      yield (ctx_partial(self.goto, self.before),
             ctx_partial(self.goto, self.loop))

      self.builder.position_at_end(self.after)

  @contextmanager
  def add_catch(self, catchall=False):
    with self.stack('catch', 'catchall'):
      self.catchall = catchall
      catch = self.catch = self.builder.append_basic_block('catch')

      def catcher(ptr, branch):
        with self.goto(catch):
          lp = self.builder.landingpad(T.lp)
          lp.add_clause(ir.CatchClause(T.ptr(T.i8)(None)))
          self.excall('rain_catch', ptr)
          self.builder.branch(branch)

      yield catcher

  @contextmanager
  def add_abort(self):
    with self.stack('catch'):
      catch = self.catch = self.builder.append_basic_block('catch')

      def aborter(branch):
        with self.goto(catch):
          lp = self.builder.landingpad(T.lp)
          lp.add_clause(ir.CatchClause(T.ptr(T.i8)(None)))
          self.excall('rain_abort')
          self.builder.branch(branch)

      yield aborter

  @contextmanager
  def goto(self, block):
    with self.builder.goto_block(block):
      yield

  @contextmanager
  def goto_entry(self):
    with self.builder.goto_entry_block():
      yield

  # Box helpers ###############################################################

  def get_type(self, box):
    return self.extract(box, T.TYPE)

  def get_value(self, box, typ=None):
    val = self.extract(box, T.DATA)
    if isinstance(typ, T.func):
      return self.builder.inttoptr(val, T.ptr(typ))

    return val

  def get_size(self, box):
    return self.extract(box, T.SIZE)

  def get_env(self, box):
    return self.extract(box, T.ENV)

  def get_vt(self, name):
    return self.find_global(T.box, 'core.types.' + name)

  def truthy(self, node):
    box = self.emit(node)
    return self.truthy_val(box)

  def truthy_val(self, val):
    typ = self.get_type(val)
    val = self.get_value(val)
    not_null = self.builder.icmp_unsigned('!=', typ, T.ityp.null)
    not_zero = self.builder.icmp_unsigned('!=', val, T.i64(0))
    return self.builder.and_(not_null, not_zero)

  # Function helpers ##########################################################

  def get_exception(self, name):
    glob = self.find_global(T.ptr(T.box), 'rain_exc_' + name)
    return self.load(glob)

  def check_callable(self, box, num_args, unwind=None):
    func_typ = self.get_type(box)
    is_func = self.builder.icmp_unsigned('!=', T.ityp.func, func_typ)
    with self.builder.if_then(is_func):
      self.excall('rain_throw', self.get_exception('uncallable'))

    exp_args = self.get_size(box)
    arg_match = self.builder.icmp_unsigned('!=', exp_args, T.i32(num_args))
    with self.builder.if_then(arg_match):
      self.excall('rain_throw', self.get_exception('arg_mismatch'))

    '''
    self.store(box, self.callable_ptr)
    self.excall('rain_check_callable', self.callable_ptr, T.i32(num_args), unwind=unwind)
    '''

  # allocate stack space for function arguments
  def fnalloc(self, *args):
    with self.builder.goto_entry_block():
      if len(args) + 1 > len(self.arg_ptrs):
        for i in range(len(self.arg_ptrs), len(args) + 1):
          self.arg_ptrs.append(self.alloc(T.box, name='arg' + str(i)))

    for arg, ptr in zip(args, self.arg_ptrs):
      self.store(arg, ptr)

    return self.arg_ptrs[:len(args)]

  # allocate stack space for a function arguments, then call it
  # only used for Rain functions! (eg they only take box *)
  def fncall(self, fn, *args, unwind=None):
    ptrs = self.fnalloc(*args)
    self.call(fn, *ptrs, unwind=unwind)
    return ptrs[0]

  # call a function based on unwind
  def call(self, fn, *args, unwind=None):
    if self.catchall:
      unwind = self.catch

    if unwind:
      resume = self.builder.append_basic_block('resume')
      val = self.builder.invoke(fn, args, resume, unwind)
      self.builder.position_at_end(resume)
    else:
      val = self.builder.call(fn, args)

    return val

  # call an extern function
  def excall(self, fn, *args, unwind=None):
    return self.call(self.extern(fn), *args, unwind=unwind)

  # allocate stack space and call an extern function
  def exfncall(self, fn, *args, unwind=None):
    return self.fncall(self.extern(fn), *args, unwind=unwind)

  # llvmlite shortcuts ########################################################

  def alloc(self, typ, init=None, name=''):
    ptr = self.builder.alloca(typ, name=name)
    if init:
      self.store(init, ptr)

    return ptr

  def store(self, val, ptr):
    self.builder.store(val, ptr)

  def load(self, ptr):
    return self.builder.load(ptr)

  def insert(self, container, value, idx):
    return self.builder.insert_value(container, value, idx)

  def extract(self, container, idx):
    return self.builder.extract_value(container, idx)
