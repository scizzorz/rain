from . import ast as A

from ctypes import CFUNCTYPE, POINTER
from ctypes import Structure
from ctypes import byref
from ctypes import create_string_buffer
from ctypes import c_char_p
from ctypes import c_int
from ctypes import c_uint16
from ctypes import c_uint32
from ctypes import c_uint64
from ctypes import c_uint8
from ctypes import c_void_p
from ctypes import cast

import llvmlite.binding as llvm

class Box(Structure):
  _fields_ = [("type", c_uint8),
              ("data", c_uint64),
              ("size", c_uint32)]

  def __str__(self):
    return 'Box({}, {}, {})'.format(self.type, self.data, self.size)

  def __repr__(self):
    return '<{!s}>'.format(self)

  @classmethod
  def from_str(cls, string):
    str_p = create_string_buffer(string.encode("utf-8"))
    return cls(4, cast(str_p, c_void_p).value, len(string))

  def as_str(self):
    return cast(self.data, c_char_p).value.decode("utf-8")

Arg = POINTER(Box)

class Engine:
  def __init__(self, ll_file=None, llvm_ir=None):
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()  # yes, even this one

    # Create a target machine representing the host
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()

    # And an execution engine with a backing module
    if ll_file:
      self.main_mod = self.compile_file(ll_file)
    elif llvm_ir:
      self.main_mod = self.compile_ir(llvm_ir)
    else:
      self.main_mod = self.compile_ir('')

    self.engine = llvm.create_mcjit_compiler(self.main_mod, target_machine)

  def add_lib(self, *libs):
    for lib in libs:
      llvm.load_library_permanently(lib)

  def compile_file(self, ll_file):
    with open(ll_file) as tmp:
      return self.compile_ir(tmp.read())

  def compile_ir(self, llvm_ir):
    # Create a LLVM module object from the IR
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    return mod

  def link_file(self, *additions):
    self.link_ir(*(self.compile_file(add) for add in additions))

  def link_ir(self, *additions):
    for add in additions:
      self.main_mod.link_in(add)

  def set_main_mod(self, mod):
    self.main_mod = mod
    self.engine.add_module(mod)

  def finalize(self):
    self.engine.finalize_object()

  def get_func(self, name, *types):
    func_typ = CFUNCTYPE(*types)
    func_ptr = self.engine.get_function_address(name)
    return func_typ(func_ptr)

  def main(self):
    main = self.get_func('main', c_int, c_int, POINTER(c_char_p))

    argc = c_int(1)
    argv_0 = c_char_p("test".encode("utf-8"))

    main(argc, byref(argv_0))


  # rain_get

  def rain_get(self, table_box, key_box):
    get = self.get_func('rain_get', Arg, Arg, Arg)  # ret, table, key
    ret_box = Box(0, 0, 0)
    get(byref(ret_box), byref(table_box), byref(key_box))
    return ret_box

  def rain_get_str(self, table_box, key):
    return self.rain_get(table_box, Box.from_str(key))

  def rain_get_int(self, table_box, key):
    return self.rain_get(table_box, Box(1, key, 0))


  # rain_put

  def rain_put(self, table_box, key_box, value_box):
    put = self.get_func('rain_put', Arg, Arg, Arg)  # table, key, val
    put(byref(table_box), byref(key_box), byref(value_box))

  def rain_put_str(self, table_box, key, value_box):
    key_box = Box.from_str(key)
    self.rain_put(table_box, key_box, value_box)

  def rain_put_int(self, table_box, key, value_box):
    self.rain_put(table_box, Box(1, key, 0), value_box)

  def rain_set_table(self, table_box):
    set_table = self.get_func('rain_set_table', Arg)
    set_table(byref(table_box))

  # converting between Rain and Python AST

  def to_rain(self, val):
    if val is None:
      return Box(0, 0, 0)

    elif val is True:
      return Box(3, 1, 0)

    elif val is False:
      return Box(3, 0, 0)

    elif isinstance(val, int):
      return Box(1, val, 0)

    elif isinstance(val, str):
      return Box.from_str(val)

    elif isinstance(val, list):
      table_box = Box(0, 0, 0)
      self.rain_set_table(table_box)

      for i, n in enumerate(val):
        self.rain_put_int(table_box, i, self.to_rain(n))

      return table_box

    elif isinstance(val, A.node):
      table_box = Box(0, 0, 0)
      self.rain_set_table(table_box)

      self.rain_put_str(table_box, 'tag', Box.from_str(val.__tag__))
      for key in val.__slots__:
        self.rain_put_str(table_box, key, self.to_rain(getattr(val, key, None)))

      tag_out = self.rain_get_str(table_box, 'tag')
      return table_box

    return "Can't convert value to Rain: {!r}".format(val)

  def to_py(self, box):
    if box.type == 0:
      return None

    elif box.type == 1:
      return box.data

    elif box.type == 3:
      return bool(box.data)

    elif box.type == 4:
      return box.as_str()

    elif box.type == 5:
      tag = self.to_py(self.rain_get_str(box, "tag"))
      if tag:
        node_type = A.tag_registry[tag]
        slots = [self.to_py(self.rain_get_str(box, slot)) for slot in node_type.__slots__]

        return node_type(*slots)

      else:
        res = []
        i = 0
        while True:
          next = self.to_py(self.rain_get_int(box, i))
          if next is None:
            break

          res.append(next)
          i += 1

        return res
