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
  with module.rvm.goto(module.rvm.main):
    for stmt in self.stmts:
      stmt.emit(module)
    module.rvm.ret()


@A.block_node.method
def emit(self, module):
  for stmt in self.stmts:
    stmt.emit(module)

  if self.expr:
    return self.expr.emit(module)

  else:
    return T.null


# Simple statements ###########################################################

@A.assn_node.method
def emit(self, module):
  if isinstance(self.lhs, A.name_node):
    if self.var:
      module[self.lhs] = True

    if self.lhs not in module:
      Q.abort('Undeclared variable {!r}', self.lhs.value, pos=self.lhs.coords)

    if self.rhs:
      rhs = self.rhs.emit(module)
    else:
      rhs = A.null_node().emit(module)

    name = module.rvm.add_const(self.lhs.value)
    module.rvm.push_const(name)
    module.rvm.push_scope()
    module.rvm.set()


# Simple expressions ##########################################################

@A.name_node.method
def emit(self, module):
  if self.value not in module:
    #Q.abort("Unknown name {!r}", self.value, pos=self.coords)
    pass

  name = module.rvm.add_const(self.value)
  module.rvm.push_const(name)
  module.rvm.push_scope()
  module.rvm.get()


@A.null_node.method
def emit(self, module):
  idx = module.rvm.add_const(None)
  module.rvm.push_const(idx)
  return idx


@A.int_node.method
def emit(self, module):
  idx = module.rvm.add_const(self.value)
  module.rvm.push_const(idx)
  return idx


@A.float_node.method
def emit(self, module):
  idx = module.rvm.add_const(self.value)
  module.rvm.push_const(idx)
  return idx


@A.bool_node.method
def emit(self, module):
  idx = module.rvm.add_const(self.value)
  module.rvm.push_const(idx)
  return idx


@A.str_node.method
def emit(self, module):
  idx = module.rvm.add_const(self.value)
  module.rvm.push_const(idx)
  return idx


@A.table_node.method
def emit(self, module):
  module.rvm.push_table()


@A.func_node.method
def emit(self, module):
  fn = module.rvm.add_block()
  with module.rvm.goto(fn):
    self.body.emit(module)
    module.rvm.ret()

  fn_ptr = module.rvm.add_const(lambda: fn.addr)
  module.rvm.push_const(fn_ptr)
  module.rvm.push_table()
  module.rvm.push_scope()
  module.rvm.set_meta()
  module.rvm.set_meta()


# Compound expressions ########################################################

@A.call_node.method
def emit(self, module):
  for arg in self.args:
    arg.emit(module)

  self.func.emit(module)
  module.rvm.call()


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
