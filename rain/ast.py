import camel
import fixedint

registry = camel.CamelRegistry()
machine = camel.Camel([registry])

# Base classes

class metanode(type):
  def method(cls, func):
    setattr(cls, func.__name__, func)
    return func

  def __init__(cls, name, bases, attrs):
    super().__init__(name, bases, attrs)
    registry.dumper(cls, cls.__tag__, version=cls.__version__)(cls.dump)
    registry.loader(cls.__tag__, version=cls.__version__)(cls.load)

  def dump(cls, self):
    return {slot: getattr(self, slot) for slot in cls.__slots__}

  def load(cls, data, version):
    return cls(*(data[slot] for slot in cls.__slots__))

  def __str__(self):
    return self.__name__

  def __repr__(self):
    return '<{}>'.format(self.__name__)

class node(metaclass=metanode):
  __tag__ = 'node'
  __version__ = 1
  __slots__ = []

  def __str__(self):
    return str(type(self))

  def __repr__(self):
    return repr(type(self))

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

  def __str__(self):
    return '{}({!r})'.format(type(self), self.value)

  def __repr__(self):
    return '<{!s}>'.format(self)

# structure

class program_node(node):
  __tag__ = 'program'
  __version__ = 1
  __slots__ = ['stmts']

  def __init__(self, stmts=[]):
    self.stmts = stmts

  def __str__(self):
    return '; '.join(str(x) for x in self.stmts)

class block_node(node):
  __tag__ = 'block'
  __version__ = 1
  __slots__ = ['stmts']

  def __init__(self, stmts=[]):
    self.stmts = stmts

  def __str__(self):
    return '; '.join(str(x) for x in self.stmts)

# statements

class assn_node(node):
  __tag__ = 'assn'
  __version__ = 1
  __slots__ = ['lhs', 'rhs', 'let']

  def __init__(self, lhs, rhs, let=False):
    self.lhs = lhs
    self.rhs = rhs
    self.let = let

  def __str__(self):
    return 'assn {!s} = {!s}'.format(self.lhs, self.rhs)

class break_node(node):
  __tag__ = 'break'
  __version__ = 1
  __slots__ = ['cond']

  def __init__(self, cond=None):
    self.cond = cond

class catch_node(node):
  __tag__ = 'catch'
  __version__ = 1
  __slots__ = ['name', 'body']

  def __init__(self, name, body):
    self.name = name
    self.body = body

class cont_node(node):
  __tag__ = 'continue'
  __version__ = 1
  __slots__ = ['cond']

  def __init__(self, cond=None):
    self.cond = cond

class export_node(node):
  __tag__ = 'export'
  __version__ = 1
  __slots__ = ['val', 'name']

  def __init__(self, val, name):
    self.val = val
    self.name = name

  def __str__(self):
    return 'export({!s} as {!s})'.format(self.val, self.name)

class if_node(node):
  __tag__ = 'if'
  __version__ = 1
  __slots__ = ['pred', 'body', 'els']

  def __init__(self, pred, body, els=None):
    self.pred = pred
    self.body = body
    self.els = els

  def __str__(self):
    return 'if {!s} {{ {!s} }} else {{ {!s} }}'.format(self.pred, self.body, self.els)

class loop_node(node):
  __tag__ = 'loop'
  __version__ = 1
  __slots__ = ['body']

  def __init__(self, body):
    self.body = body

  def __str__(self):
    return 'loop {{ {!s} }}'.format(self.body)

class pass_node(node):
  __tag__ = 'pass'

class return_node(value_node):
  __tag__ = 'return'

class save_node(value_node):
  __tag__ = 'save'

class until_node(node):
  __tag__ = 'until'
  __version__ = 1
  __slots = ['pred', 'body']

  def __init__(self, pred, body):
    self.pred = pred
    self.body = body

  def __str__(self):
    return 'until {!s} {{ {!s} }}'.format(self.pred, self.body)

class while_node(node):
  __tag__ = 'while'
  __version__ = 1
  __slots = ['pred', 'body']

  def __init__(self, pred, body):
    self.pred = pred
    self.body = body

  def __str__(self):
    return 'while {!s} {{ {!s} }}'.format(self.pred, self.body)

class for_node(node):
  __tag__ = 'for'
  __version__ = 1
  __slots = ['name', 'func', 'body']

  def __init__(self, name, func, body):
    self.name = name
    self.func = func
    self.body = body

  def __str__(self):
    return 'for {!s} in {!s} {{ {!s} }}'.format(self.name, self.func, self.body)

class with_node(node):
  __tag__ = 'with'
  __version__ = 1
  __slots = ['expr', 'params', 'body']

  def __init__(self, expr, params, body):
    self.expr = expr
    self.params = params
    self.body = body

# expressions

class idx_node(node):
  __tag__ = 'index'
  __version__ = 1
  __slots__ = ['lhs', 'rhs']

  def __init__(self, lhs, rhs):
    self.lhs = lhs
    self.rhs = rhs

class name_node(value_node):
  __tag__ = 'name'

class literal_node:
  def hash(self):
    raise Exception("Can't hash {!s}".format(self))

class null_node(node, literal_node):
  __tag__ = 'null'

  def hash(self):
    return 0

class int_node(value_node, literal_node):
  __tag__ = 'int'

  def hash(self):
    return int(fixedint.UInt64(self.value))

class float_node(value_node, literal_node):
  __tag__ = 'float'

  def hash(self):
    return int(ctypes.c_int.from_buffer(ctypes.c_float(1.0)).value)

class bool_node(value_node, literal_node):
  __tag__ = 'bool'

  def hash(self):
    return int(self.value)

class str_node(value_node, literal_node):
  __tag__ = 'str'

  def hash(self):
    val = fixedint.MutableUInt64(0)
    for char in self.value:
      val += ord(char)
    return int(val)

class table_node(node):
  __tag__ = 'table'
  __version__ = 1
  __slots__ = ['metatable']

  def __init__(self, metatable=None):
    self.metatable = metatable

class extern_node(node):
  __tag__ = 'extern'
  __version__ = 1
  __slots__ = ['name']

  def __init__(self, name):
    self.name = name

  def __str__(self):
    return 'extern({!s})'.format(self.name)

class import_node(node):
  __tag__ = 'import'
  __version__ = 1
  __slots__ = ['name', 'rename']

  def __init__(self, name, rename=None):
    self.name = name
    self.rename = rename

  def __str__(self):
    return 'import({!s})'.format(self.name)

class func_node(node):
  __tag__ = 'func'
  __version__ = 1
  __slots__ = ['params', 'body']

  def __init__(self, params, body):
    self.params = params
    self.body = body

  def __str__(self):
    return 'func({!s}) {{ {!s} }}'.format(', '.join(str(x) for x in self.params), self.body)

class call_node(node):
  __tag__ = 'call'
  __version__ = 1
  __slots__ = ['func', 'args', 'catch']

  def __init__(self, func, args, catch=False):
    self.func = func
    self.args = args
    self.catch = catch

  def __str__(self):
    return '{!s}({!s})'.format(self.func, ', '.join(str(x) for x in self.args))

class meth_node(node):
  __tag__ = 'method'
  __version__ = 1
  __slots__ = ['lhs', 'rhs', 'args', 'catch']

  def __init__(self, lhs, rhs, args, catch=False):
    self.lhs = lhs
    self.rhs = rhs
    self.args = args
    self.catch = catch

  def __str__(self):
    return '{!s}:{!s}({!s})'.format(self.lhs, self.rhs, ', '.join(str(x) for x in self.args))

class bind_node(node):
  __tag__ = 'binding'
  __version__ = 1
  __slots__ = ['lhs', 'rhs']

  def __init__(self, lhs, rhs):
    self.lhs = lhs
    self.rhs = rhs

  def __str__(self):
    return '{!s}:{!s}'.format(self.lhs, self.rhs)

class is_node(node):
  __tag__ = 'is'
  __version__ = 1
  __slots__ = ['lhs', 'typ']

  def __init__(self, lhs, typ):
    self.lhs = lhs
    self.typ = typ

  def __str__(self):
    return '{!s} is {!s}'.format(self.lhs, self.typ)

class binary_node(node):
  __tag__ = 'binary'
  __version__ = 1
  __slots__ = ['lhs', 'rhs', 'op']

  def __init__(self, lhs, rhs, op):
    self.lhs = lhs
    self.rhs = rhs
    self.op = op

  def __str__(self):
    return '({!s} {!s} {!s})'.format(self.lhs, self.op, self.rhs)

class unary_node(node):
  __tag__ = 'unary'
  __version__ = 1
  __slots__ = ['op', 'val']

  def __init__(self, op, val):
    self.op = op
    self.val = val

  def __str__(self):
    return '({!s}{!s})'.format(self.op, self.val)
