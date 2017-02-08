from ctypes import CFUNCTYPE, POINTER
from ctypes import Structure
from ctypes import byref
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

  @classmethod
  def from_str(cls, string):
    str_p = c_char_p(string.encode("utf-8"))
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

  def rain_get_str(self, table_box, key):
    get = self.get_func('rain_get', Arg, Arg, Arg)
    ret_box = Box(0, 0, 0)
    key_str = c_char_p(key.encode("utf-8"))
    key_box = Box(4, cast(key_str, c_void_p).value, len(key))

    get(byref(ret_box), byref(table_box), byref(key_box))
    return ret_box

  def main(self):
    main = self.get_func('main', c_int, c_int, POINTER(c_char_p))

    argc = c_int(1)
    argv_0 = c_char_p("test".encode("utf-8"))

    main(argc, byref(argv_0))
