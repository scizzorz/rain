from . import ast as A
from . import runtime
from . import scope as S
from . import static
from . import token as K
from . import types as T
from contextlib import contextmanager
import rvmpy
from llvmlite import binding
from llvmlite import ir
from os.path import isdir, isfile
from os.path import join
import os.path
import re

name_chars = re.compile('[^a-z0-9]')

TRACE_MAIN = -1
TRACE_INIT = -2
TRACE_UNKNOWN = -3


# get default paths
def get_paths():
  path = os.environ['RAINPATH'].split(':') if 'RAINPATH' in os.environ else []
  core = [os.environ['RAINBASE'], os.environ['RAINLIB']]
  return path + core


# normalize a name - remove all special characters and cases
def normalize_name(name):
  return name_chars.sub('', name.lower())


# find a rain file from a module identifier
def find_rain(src, paths=[]):
  if src[0] == '/':
    paths = ['']
  elif src[0] != '.':
    paths = get_paths() + paths

  for path in paths:
    if isfile(join(path, src) + '.rn'):
      return join(path, src) + '.rn'
    elif isfile(join(path, src)) and src.endswith('.rn'):
      return join(path, src)
    elif isdir(join(path, src)) and isfile(join(path, src, '_pkg.rn')):
      return join(path, src, '_pkg.rn')


# find any file from a string
def find_file(src, paths=[]):
  if src[0] == '/':
    paths = ['']
  elif src[0] != '.':
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

    self.rvm = rvmpy.Module(name=self.qname)

    self.builder = None
    self.arg_ptrs = None
    self.landingpad = None
    self.before = None
    self.loop = None
    self.after = None
    self.ret_ptr = None
    self.bind_ptr = None
    self.bindings = None

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

  # save and restore some module attributes around a code block
  @contextmanager
  def stack(self, *attrs):
    saved = [getattr(self, attr) for attr in attrs]
    yield
    for attr, val in zip(attrs, saved):
      setattr(self, attr, val)

  # generate a unique name
  def uniq(self, name):
    ret = self.mangle('{}.{}'.format(name, self.name_counter))
    self.name_counter += 1
    return ret

  # Global helpers ############################################################

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
      yield

  @contextmanager
  def add_func_body(self, func):
    with self.stack('ret_ptr', 'bind_ptr', 'arg_ptrs', 'landingpad', 'bindings'):
      entry = func.append_basic_block('entry')
      body = func.append_basic_block('body')
      self.bindings = set()
      self.ret_ptr = func.args[0]
      self.arg_ptrs = []
      self.landingpad = None
      with self.add_builder(entry):
        # create a pointer using the incoming binding data
        if self.ret_ptr.type == T.arg:
          self.bind_ptr = self.alloc()
          self.store(self.load(self.ret_ptr), self.bind_ptr)
          self.store(T.null, self.ret_ptr)

        self.builder.branch(body)

      with self.add_builder(body):
        yield

  @contextmanager
  def add_loop(self):
    with self.stack('before', 'loop', 'after'):
      self.before = self.builder.append_basic_block('before')
      self.loop = self.builder.append_basic_block('loop')
      self.after = self.builder.append_basic_block('after')

      self.builder.branch(self.before)

      yield

      self.builder.position_at_end(self.after)

  @contextmanager
  def add_catch(self):
    with self.stack('landingpad'):
      self.landingpad = self.builder.append_basic_block('catch')
      yield

  def catch(self, branch, into=None):
    with self.goto(self.landingpad):
      lp = self.builder.landingpad(T.lp)
      lp.add_clause(ir.CatchClause(T.ptr(T.i8)(None)))

      if into:
        self.runtime.catch(into)
      else:
        self.runtime.abort()

      self.builder.branch(branch)

  @contextmanager
  def goto(self, block):
    with self.builder.goto_block(block):
      yield

  @contextmanager
  def goto_entry(self):
    with self.builder.goto_entry_block():
      yield

  @contextmanager
  def trace(self, pos, mod=None):
    label = mod or self.name_ptr
    line, col = TRACE_UNKNOWN, TRACE_UNKNOWN

    if pos:
      line, col = pos.line, pos.col

    self.builder.call(self.runtime['push'], (label, T.i32(line), T.i32(col)))
    yield
    self.builder.call(self.runtime['pop'], ())

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
    return self.find_global(T.box, 'core.types.' + name + '.module')

  def load_exception(self, name):
    glob = self.find_global(T.ptr(T.box), 'rain_exc_' + name)
    return self.load(glob)

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

  def check_callable(self, box, num_args):
    func_typ = self.get_type(box)
    is_func = self.builder.icmp_unsigned('!=', T.ityp.func, func_typ)
    with self.builder.if_then(is_func):
      self.runtime.panic(self.load_exception('uncallable'))

    exp_args = self.get_size(box)
    arg_match = self.builder.icmp_unsigned('!=', exp_args, T.i32(num_args))
    with self.builder.if_then(arg_match):
      self.runtime.panic(self.load_exception('arg_mismatch'))

  # allocate stack space for function arguments
  def fnalloc(self, *args):
    with self.builder.goto_entry_block():
      if len(args) + 1 > len(self.arg_ptrs):
        for i in range(len(self.arg_ptrs), len(args) + 1):
          self.arg_ptrs.append(self.alloc(name='arg' + str(i)))

    for arg, ptr in zip(args, self.arg_ptrs):
      self.store(arg, ptr)

    return self.arg_ptrs[:len(args)]

  # call a function based on whether there's a landingpad or not
  def call(self, fn, *args):
    if self.landingpad:
      resume = self.builder.append_basic_block('resume')
      val = self.builder.invoke(fn, args, resume, self.landingpad)
      self.builder.position_at_end(resume)

    else:
      val = self.builder.call(fn, args)

    return val

  # call a function from a box
  def box_call(self, func_box, arg_boxes=(), catch=False, check_env=True):
    # load the pointer
    func_ptr = self.get_value(func_box, typ=T.vfunc(var_arg=True))

    # ensure it's callable - panic otherwise
    self.check_callable(func_box, len(arg_boxes))

    # allocate argument pointers
    ptrs = self.fnalloc(T.null, *arg_boxes)

    # load the function's closure environment
    if check_env:
      env = self.get_env(func_box)
      has_env = self.builder.icmp_unsigned('!=', env, T.arg(None))
      with self.builder.if_then(has_env):
        env_box = self.load(env)
        self.store(env_box, ptrs[0])

    # catch call
    if catch:
      # make a note of the call stack depth
      trace_depth_val = self.load(self.trace_depth)

      with self.add_catch():
        self.call(func_ptr, *ptrs)
        self.catch(self.builder.block, into=ptrs[0])

      # restore call stack depth
      self.store(trace_depth_val, self.trace_depth)

      return self.load(ptrs[0])

    # regular call
    else:
      self.call(func_ptr, *ptrs)
      return self.load(ptrs[0])

  # llvmlite shortcuts ########################################################

  def alloc(self, init=None, name='', typ=T.box):
    ptr = self.builder.alloca(typ, name=name)
    if init:
      self.store(init, ptr)

    return ptr

  def store(self, val, ptr):
    self.builder.store(val, ptr)

  def load(self, ptr):
    return self.builder.load(ptr)

  def store_global(self, value, name):
    self[name].initializer = value

  def load_global(self, name):
    return self[name].initializer

  def insert(self, container, value, idx):
    return self.builder.insert_value(container, value, idx)

  def extract(self, container, idx):
    return self.builder.extract_value(container, idx)

  def unpack(self, source, structure):
    values = []
    for i, sub in enumerate(structure):
      ptr, *args = self.fnalloc(T.null, source, A.int_node(i).emit(self))
      self.runtime.get(ptr, *args)
      value = self.load(ptr)
      if isinstance(sub, list):
        value = self.unpack(value, sub)
      values.append(value)

    return values
