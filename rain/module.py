from contextlib import contextmanager
from llvmlite import binding
from llvmlite import ir
import os
import re

from . import types as T
from . import scope as S

name_chars = re.compile('[^a-z0-9]')

externs = {
  'GC_malloc': T.func(T.ptr(T.i8), [T.i32]),

  'rain_box_to_exit': T.func(T.i32, [T.ptr(T.box)]),
  'rain_print': T.func(T.void, [T.ptr(T.box)]),

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

  'rain_new_table': T.func(T.ptr(T.box), []),
  'rain_new_pair': T.func(T.void, [T.ptr(T.box), T.ptr(T.box)]),
  'rain_put': T.bin,
  'rain_get': T.bin,
}

# partially apply a context manager
@contextmanager
def ctx_partial(func, *args, **kwargs):
  with func(*args, **kwargs) as val:
    yield val

class Module(S.Scope):
  def __init__(self, name):
    S.Scope.__init__(self)

    self.name = name
    self.llvm = ir.Module(name=self.name)
    self.llvm.triple = binding.get_default_triple()

    self.entry = None
    self.builder = None
    self.before = None
    self.loop = None
    self.after = None
    self.ret_ptr = None

    self.name_counter = 0

  @property
  def ir(self):
    return str(self.llvm)

  def __str__(self):
    return 'Module {!r}'.format(self.name)

  def __repr__(self):
    return '<{!s}>'.format(self)

  # save and restore some module attributes around a code block
  @contextmanager
  def stack(self, *attrs):
    saved = [getattr(self, attr) for attr in attrs]
    yield
    for attr, val in zip(attrs, saved):
      setattr(self, attr, val)

  # save and restore a new builder
  @contextmanager
  def add_builder(self, block):
    with self.stack('builder'):
      self.builder = ir.IRBuilder(block)
      yield self.builder

  # main function
  @property
  def main(self):
    typ = T.func(T.i32, (T.ptr(T.ptr(T.i8)), T.i32))
    return self.find_func(typ, name='main')

  # add a new function
  def add_func(self, typ, name=None):
    if not name:
      name = self.uniq('func')
    return ir.Function(self.llvm, typ, name=name)

  # add a new global
  def add_global(self, typ, name=None):
    if not name:
      name = self.uniq('glob')
    return ir.GlobalVariable(self.llvm, typ, name=name)

  # add or get an existing function
  def find_func(self, typ, name):
    if name in self.llvm.globals:
      return self.llvm.get_global(name)

    return self.add_func(typ, name=name)

  # add or find an external function
  def extern(self, name):
    return self.find_func(externs[name], name=name)

  # add a function body block
  @contextmanager
  def add_func_body(self, func):
    with self.stack('entry', 'ret_ptr'):
      self.entry = func.append_basic_block('entry')
      self.ret_ptr = func.args[0]
      with self.add_builder(self.entry):
        yield

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
  def add_main(self):
    block = self.main.append_basic_block(name='entry')
    with self.add_builder(block):
      yield self.main

  @contextmanager
  def goto(self, block):
    with self.builder.goto_block(block):
      yield

  # normalize a name - remove all special characters and cases
  @staticmethod
  def normalize_name(name):
    return name_chars.sub('', name.lower())

  # find a module name
  @staticmethod
  def find_name(src):
    path, name = os.path.split(src)
    fname, ext = os.path.splitext(name)

    return Module.normalize_name(fname)

  # mangle a name
  def mangle(self, name):
    return self.name + '.' + name

  # generate a unique name
  def uniq(self, name):
    ret = self.mangle('{}.{}'.format(name, self.name_counter))
    self.name_counter += 1
    return ret
