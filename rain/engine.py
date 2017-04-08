from . import ast as A
from . import types as T
from . import error as Q
import ctypes as ct
import llvmlite.binding as llvm


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

  def add_ir(self, llvm_ir):
    self.engine.add_module(self.compile_ir(llvm_ir))

  def finalize(self):
    self.engine.finalize_object()

  def get_func(self, name, *types):
    func_typ = ct.CFUNCTYPE(*types)
    func_ptr = self.engine.get_function_address(name)
    return func_typ(func_ptr)

  def get_global(self, name, typ):
    addr = self.engine.get_global_value_address(name)
    ptr = ct.cast(ct.c_void_p(addr), typ)
    return ptr

  def main(self):
    main = self.get_func('main', ct.c_int, ct.c_int, ct.POINTER(ct.c_char_p))

    argc = ct.c_int(1)
    argv_0 = ct.c_char_p("test".encode("utf-8"))

    return main(argc, ct.byref(argv_0))

  def enable_gc(self):
    enable_gc = self.get_func('rain_enable_gc', ct.c_int)
    enable_gc()

  def disable_gc(self):
    disable_gc = self.get_func('rain_disable_gc', ct.c_int)
    disable_gc()

  def init_gc(self):
    init_gc = self.get_func('rain_init_gc', ct.c_int)
    init_gc()

  def init_ast(self):
    init_ast = self.get_func('rain.ast.init', T.carg)
    ret_box = T.cbox.to_rain(None)
    init_ast(ct.byref(ret_box))


  # rain_get

  def rain_get(self, table_box, key_box):
    get = self.get_func('rain_get', T.carg, T.carg, T.carg)  # ret, table, key
    ret_box = T.cbox.to_rain(None)
    get(ct.byref(ret_box), ct.byref(table_box), ct.byref(key_box))
    return ret_box

  def rain_get_py(self, table_box, key):
    return self.rain_get(table_box, T.cbox.to_rain(key))

  def rain_get_ptr(self, table_ptr, key_box):
    get_ptr = self.get_func('rain_get_ptr', T.carg, T.carg, T.carg)
    return get_ptr(table_ptr, ct.byref(key_box))

  def rain_get_ptr_py(self, table_ptr, key):
    return self.rain_get_ptr(table_ptr, T.cbox.to_rain(key))


  # rain_put

  def rain_put(self, table_box, key_box, value_box):
    put = self.get_func('rain_put', T.carg, T.carg, T.carg)  # table, key, val
    put(ct.byref(table_box), ct.byref(key_box), ct.byref(value_box))

  def rain_put_py(self, table_box, key, value_box):
    key_box = T.cbox.to_rain(key)
    self.rain_put(table_box, key_box, value_box)

  def rain_set_table(self, table_box):
    set_table = self.get_func('rain_set_table', T.carg)
    set_table(ct.byref(table_box))


  # set environment

  def rain_set_env(self, table_box, meta_ptr):
    set_meta = self.get_func('rain_set_env', T.carg, T.carg)
    set_meta(ct.byref(table_box), meta_ptr)


  # converting between Rain and Python AST

  def to_rain(self, val):
    if isinstance(val, (list, tuple)):
      table_box = T.cbox.to_rain(None)
      self.rain_set_table(table_box)

      ast_ptr = self.get_global('core.ast.exports', T.carg)
      meta_ptr = self.rain_get_ptr_py(ast_ptr, 'list')
      self.rain_set_env(table_box, meta_ptr)

      for i, n in enumerate(val):
        self.rain_put_py(table_box, i, self.to_rain(n))

      return table_box

    elif isinstance(val, A.node):
      table_box = T.cbox.to_rain(None)
      self.rain_set_table(table_box)

      ast_ptr = self.get_global('core.ast.exports', T.carg)
      meta_ptr = self.rain_get_ptr_py(ast_ptr, val.__tag__)
      self.rain_set_env(table_box, meta_ptr)

      slots = [self.to_rain(getattr(val, key, None)) for key in val.__slots__]

      tag_in = T.cbox.to_rain(val.__tag__)
      self.rain_put_py(table_box, 'tag', tag_in)

      for key, box in zip(val.__slots__, slots):
        self.rain_put_py(table_box, key, box)

      return table_box

    return T.cbox.to_rain(val)

  def to_py(self, box):
    if box.type == T.typi.table:
      tag_box = self.rain_get_py(box, 'tag')
      tag = self.to_py(tag_box)

      if tag:
        node_type = A.tag_registry[tag]
        slots = [self.to_py(self.rain_get_py(box, slot)) for slot in node_type.__slots__]

        return node_type(*slots)

      else:
        res = []
        i = 0
        while True:
          next = self.to_py(self.rain_get_py(box, i))
          if next is None:
            break

          res.append(next)
          i += 1

        return res

    return box.to_py()
