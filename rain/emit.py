from . import ast as A
from . import error as Q


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
  with module.goto(module.main):
    for stmt in self.stmts:
      stmt.emit(module)
    module.ret()


@A.block_node.method
def emit(self, module):
  for stmt in self.stmts:
    stmt.emit(module)


# Simple statements ###########################################################

@A.assn_node.method
def emit(self, module):
  if isinstance(self.lhs, A.name_node):
    if self.rhs:
      self.rhs.emit(module)
    else:
      A.null_node().emit(module)

    name = module.add_const(self.lhs.value)
    module.push_const(name)
    module.push_scope()
    module.set()

  elif isinstance(self.lhs, A.idx_node):
    self.rhs.emit(module)
    self.lhs.rhs.emit(module)
    self.lhs.lhs.emit(module)
    module.set()


@A.return_node.method
def emit(self, module):
  if self.value:
    self.value.emit(module)
  else:
    A.null_node().emit(module)

  module.save()


# Compound statements #########################################################

@A.if_node.method
def emit(self, module):
  self.pred.emit(module)

  if self.els:
    body = module.ins_block()
    after = module.ins_block()
    module.jump_if(body)
    self.els.emit(module)
    module.jump(after)

    with module.goto(body):
      self.body.emit(module)
      module.jump(after)

    module.block = after

  else:
    body = module.ins_block()
    after = module.ins_block()
    module.jump_if(body)
    module.jump(after)

    with module.goto(body):
      self.body.emit(module)
      module.jump(after)

    module.block = after


# Simple expressions ##########################################################

@A.name_node.method
def emit(self, module):
  name = module.add_const(self.value)
  module.push_const(name)
  module.push_scope()
  module.get()


@A.null_node.method
def emit(self, module):
  idx = module.add_const(None)
  module.push_const(idx)
  return idx


@A.int_node.method
def emit(self, module):
  idx = module.add_const(self.value)
  module.push_const(idx)
  return idx


@A.float_node.method
def emit(self, module):
  idx = module.add_const(self.value)
  module.push_const(idx)
  return idx


@A.bool_node.method
def emit(self, module):
  idx = module.add_const(self.value)
  module.push_const(idx)
  return idx


@A.str_node.method
def emit(self, module):
  idx = module.add_const(self.value)
  module.push_const(idx)
  return idx


@A.table_node.method
def emit(self, module):
  module.push_table()


@A.func_node.method
def emit(self, module):
  fn = module.add_block()
  with module.goto(fn):
    module.fit(len(self.params))

    for param in reversed(self.params):
      param_name = module.add_const(param)
      module.push_const(param_name)
      module.push_scope()
      module.set()

    self.body.emit(module)
    module.ret()

  fn_ptr = module.add_const(lambda: fn.addr)
  module.push_const(fn_ptr)
  module.push_table()
  module.push_scope()
  module.set_meta()
  module.set_meta()


# Compound expressions ########################################################

@A.call_node.method
def emit(self, module):
  for arg in self.args:
    arg.emit(module)

  self.func.emit(module)
  module.call(len(self.args))

  if self.pop:
    module.pop()


@A.binary_node.method
def emit(self, module):
  ops = {
    '+': module.add,
    '-': module.sub,
    '*': module.mul,
    '/': module.div,
    '<': module.lt,
    '>': module.gt,
    '<=': module.le,
    '>=': module.ge,
    '!=': module.ne,
    '==': module.eq,
    '::': module.set_meta,
  }

  self.lhs.emit(module)
  self.rhs.emit(module)

  if self.op not in ops:
    Q.abort("Invalid binary operator", pos=self.coords)

  ops[self.op]()


@A.idx_node.method
def emit(self, module):
  self.rhs.emit(module)
  self.lhs.emit(module)
  module.get()


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
