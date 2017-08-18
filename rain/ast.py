from . import error as Q
import camel

registry = camel.CamelRegistry()
machine = camel.Camel([registry])
tag_registry = {}


# Base classes ################################################################

class metanode(type):
  def method(cls, func):
    setattr(cls, func.__name__, func)
    return func

  def __init__(cls, name, bases, attrs):
    super().__init__(name, bases, attrs)
    registry.dumper(cls, cls.__tag__, version=cls.__version__)(cls.dump)
    registry.loader(cls.__tag__, version=cls.__version__)(cls.load)
    tag_registry[cls.__tag__] = cls

  def dump(cls, self):
    return {slot: getattr(self, slot) for slot in cls.__slots__}

  def load(cls, data, version):
    return cls(*(data[slot] for slot in cls.__slots__))

  def __str__(self):
    return self.__name__

  def __repr__(self):
    return '<{!s}>'.format(self)


class node(metaclass=metanode):
  __tag__ = 'node'
  __version__ = 1
  __slots__ = ['_coords']

  @property
  def coords(self):
    return getattr(self, '_coords', None)

  @coords.setter
  def coords(self, value):
    self._coords = value

  def emit(self, module):
    Q.abort("Can't emit bytecode for {!r}", self, pos=self.coords)

  def __str__(self):
    args = ', '.join(['{!s}={!s}'.format(key, getattr(self, key)) for key in self.__slots__])
    return '{!s}({!s})'.format(type(self).__name__, args)

  def __repr__(self):
    return '<{!s}>'.format(self)


class value_node(node):
  __tag__ = 'value'
  __version__ = 1
  __slots__ = ['value']

  def __init__(self, value=None):
    self.value = value

  def __eq__(self, other):
    if type(self) != type(other):
      return False

    return self.value == other.value


class expr_node(node):
  __slots__ = []


# Structure ###################################################################

class program_node(node):
  __tag__ = 'program'
  __version__ = 1
  __slots__ = ['stmts']

  def __init__(self, stmts=[]):
    self.stmts = stmts

  def emit(self, module):
    with module.goto(module.main):
      for stmt in self.stmts:
        stmt.emit(module)
      module.ret()


class block_node(expr_node):
  __tag__ = 'block'
  __version__ = 2
  __slots__ = ['stmts', 'expr']

  def __init__(self, stmts=[], expr=None):
    self.stmts = stmts
    self.expr = expr

  def emit(self, module):
    for stmt in self.stmts:
      stmt.emit(module)


# Statements ##################################################################

class assn_node(node):
  __tag__ = 'assn'
  __version__ = 4
  __slots__ = ['lhs', 'rhs', 'var']

  def __init__(self, lhs, rhs, var=False):
    self.lhs = lhs
    self.rhs = rhs
    self.var = var

  def emit(self, module):
    if isinstance(self.lhs, name_node):
      if self.rhs:
        self.rhs.emit(module)
      else:
        null_node().emit(module)

      name = module.add_const(self.lhs.value)
      module.push_const(name)
      module.push_scope()
      module.set()

    elif isinstance(self.lhs, idx_node):
      self.rhs.emit(module)
      self.lhs.rhs.emit(module)
      self.lhs.lhs.emit(module)
      module.set()

    elif isinstance(self.lhs, list):
      self.rhs.emit(module)
      module.unpack(self.lhs)

    else:
      Q.abort('Not able to handle assignment')


class bind_node(node):
  __tag__ = 'bind'
  __version__ = 1
  __slots__ = ['names']

  def __init__(self, names):
    self.names = names


class break_node(node):
  __tag__ = 'break'
  __version__ = 1
  __slots__ = ['cond']

  def __init__(self, cond=None):
    self.cond = cond


class catch_node(node):
  __tag__ = 'catch'
  __version__ = 2
  __slots__ = ['body']

  def __init__(self, body):
    self.body = body

  def emit(self, module):
    exit = module.ins_block()
    module.catch_push()
    module.jump(exit)
    self.body.emit(module)
    null_const = module.add_const(None)
    module.push_const(null_const)
    module.catch_pop()
    module.block = exit


class cont_node(node):
  __tag__ = 'continue'
  __version__ = 1
  __slots__ = ['cond']

  def __init__(self, cond=None):
    self.cond = cond


class for_node(node):
  __tag__ = 'for'
  __version__ = 3
  __slots__ = ['name', 'func', 'body']

  def __init__(self, name, func, body):
    self.name = name
    self.func = func
    self.body = body

  def emit(self, module):
    entry = module.ins_block()
    exit = module.ins_block()

    none_const = module.add_const(None)
    self.func.emit(module)
    module.jump(entry)

    with module.goto(entry):
      module.dup()
      module.call(0)
      module.dup()
      module.push_const(none_const)
      module.eq()
      module.jump_if(exit)

      if isinstance(self.name, list):
        module.unpack(self.name)
      else:
        name_const = module.add_const(self.name.value)
        module.push_const(name_const)
        module.push_scope()
        module.set()

      self.body.emit(module)
      module.jump(entry)

    module.block = exit
    module.pop()


class if_node(node):
  __tag__ = 'if'
  __version__ = 1
  __slots__ = ['pred', 'body', 'els']

  def __init__(self, pred, body, els=None):
    self.pred = pred
    self.body = body
    self.els = els

  def emit(self, module):
    self.pred.emit(module)

    if self.els:
      els = module.ins_block()
      after = module.ins_block()

      module.jump_not(els)

      self.body.emit(module)
      module.jump(after)

      with module.goto(els):
        self.els.emit(module)
        module.jump(after)

      module.block = after

    else:
      after = module.ins_block()
      module.jump_not(after)
      self.body.emit(module)
      module.jump(after)

      module.block = after


class loop_node(node):
  __tag__ = 'loop'
  __version__ = 1
  __slots__ = ['body']

  def __init__(self, body):
    self.body = body


class pass_node(node):
  __tag__ = 'pass'
  __slots__ = []

  def emit(self, module):
    pass  # beautiful


class return_node(value_node):
  __tag__ = 'return'

  def emit(self, module):
    if self.value:
      self.value.emit(module)
    else:
      null_node().emit(module)

    module.save()
    module.ret()


class save_node(node):
  __tag__ = 'save'
  __version__ = 2
  __slots__ = ['value', 'name']

  def __init__(self, value, name=None):
    self.value = value
    self.name = name

  def emit(self, module):
    if self.value:
      self.value.emit(module)
    else:
      null_node().emit(module)

    module.save()

    # TODO fix `save VAR = VAL`


class while_node(node):
  __tag__ = 'while'
  __version__ = 1
  __slots__ = ['pred', 'body']

  def __init__(self, pred, body):
    self.pred = pred
    self.body = body

  def emit(self, module):
    entry = module.ins_block()
    exit = module.ins_block()
    module.jump(entry)

    with module.goto(entry):
      self.pred.emit(module)
      module.jump_not(exit)
      self.body.emit(module)
      module.jump(entry)

    module.block = exit


# Expressions #################################################################

class idx_node(expr_node):
  __tag__ = 'index'
  __version__ = 1
  __slots__ = ['lhs', 'rhs']

  def __init__(self, lhs, rhs):
    self.lhs = lhs
    self.rhs = rhs

  def emit(self, module):
    self.rhs.emit(module)
    self.lhs.emit(module)
    module.get()


class name_node(value_node, expr_node):
  __tag__ = 'name'

  def emit(self, module):
    name = module.add_const(self.value)
    module.push_const(name)
    module.push_scope()
    module.get()


class null_node(expr_node):
  __tag__ = 'null'

  def emit(self, module):
    idx = module.add_const(None)
    module.push_const(idx)
    return idx


class int_node(value_node, expr_node):
  __tag__ = 'int'

  def emit(self, module):
    idx = module.add_const(self.value)
    module.push_const(idx)
    return idx


class float_node(value_node, expr_node):
  __tag__ = 'float'

  def emit(self, module):
    idx = module.add_const(self.value)
    module.push_const(idx)
    return idx


class bool_node(value_node, expr_node):
  __tag__ = 'bool'

  def emit(self, module):
    idx = module.add_const(self.value)
    module.push_const(idx)
    return idx


class str_node(value_node, expr_node):
  __tag__ = 'str'

  def emit(self, module):
    idx = module.add_const(self.value)
    module.push_const(idx)
    return idx


class table_node(expr_node):
  __tag__ = 'table'
  __version__ = 2

  def emit(self, module):
    module.push_table()


class array_node(expr_node):
  __tag__ = 'array'
  __version__ = 1
  __slots__ = ['items']

  def __init__(self, items):
    self.items = items

  def emit(self, module):
    module.push_table()

    for i, item in enumerate(self.items):
      item.emit(module)
      idx = module.add_const(i)
      module.push_const(idx)
      module.dup(2)
      module.set()

    # TODO set metatable


class dict_node(expr_node):
  __tag__ = 'dict'
  __version__ = 2
  __slots__ = ['items', 'set_meta']

  def __init__(self, items, set_meta=True):
    self.items = items
    self.set_meta = set_meta

  def emit(self, module):
    module.push_table()

    for key, value in self.items:
      value.emit(module)
      key.emit(module)
      module.dup(2)
      module.set()

    # TODO set metatable (or don't!)


class func_node(expr_node):
  __tag__ = 'func'
  __version__ = 3
  __slots__ = ['params', 'body']

  def __init__(self, params, body):
    self.params = params
    self.body = body

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


class call_node(expr_node):
  __tag__ = 'call'
  __version__ = 2
  __slots__ = ['func', 'args', 'catch', 'pop']

  def __init__(self, func, args, catch=False, pop=False):
    self.func = func
    self.args = args
    self.catch = catch
    self.pop = pop

  def emit(self, module):
    for arg in self.args:
      arg.emit(module)

    self.func.emit(module)
    module.call(len(self.args))

    if self.pop:
      module.pop()


class meth_node(expr_node):
  __tag__ = 'method'
  __version__ = 2
  __slots__ = ['lhs', 'rhs', 'args', 'catch', 'pop']

  def __init__(self, lhs, rhs, args, catch=False, pop=False):
    self.lhs = lhs
    self.rhs = rhs
    self.args = args
    self.catch = catch
    self.pop = pop

  def emit(self, module):
    self.lhs.emit(module)
    for arg in self.args:
      arg.emit(module)

    self.rhs.emit(module)
    module.dup(len(self.args) + 1)
    module.get()
    module.call(len(self.args) + 1)

    if self.pop:
      module.pop()


class binary_node(expr_node):
  __tag__ = 'binary'
  __version__ = 1
  __slots__ = ['lhs', 'rhs', 'op']

  def __init__(self, lhs, rhs, op):
    self.lhs = lhs
    self.rhs = rhs
    self.op = op

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


class unary_node(expr_node):
  __tag__ = 'unary'
  __version__ = 1
  __slots__ = ['op', 'val']

  def __init__(self, op, val):
    self.op = op
    self.val = val


# message nodes

class error_node(node):
  __tag__ = 'error'
  __version__ = 1
  __slots__ = ['msg']

  def __init__(self, msg):
    self.msg = msg

  def emit(self, module):
    Q.abort(self.msg)


class warning_node(node):
  __tag__ = 'warning'
  __version__ = 1
  __slots__ = ['msg']

  def __init__(self, msg):
    self.msg = msg

  def emit(self, module):
    Q.warn(self.msg)


class hint_node(node):
  __tag__ = 'hint'
  __version__ = 1
  __slots__ = ['msg']

  def __init__(self, msg):
    self.msg = msg

  def emit(self, module):
    Q.hint(self.msg)
