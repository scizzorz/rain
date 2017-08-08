from . import error as Q
import camel

registry = camel.CamelRegistry()
machine = camel.Camel([registry])
tag_registry = {}


# Base classes

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


# structure

class program_node(node):
  __tag__ = 'program'
  __version__ = 1
  __slots__ = ['stmts']

  def __init__(self, stmts=[]):
    self.stmts = stmts


class block_node(expr_node):
  __tag__ = 'block'
  __version__ = 2
  __slots__ = ['stmts', 'expr']

  def __init__(self, stmts=[], expr=None):
    self.stmts = stmts
    self.expr = expr


# statements

class assn_node(node):
  __tag__ = 'assn'
  __version__ = 4
  __slots__ = ['lhs', 'rhs', 'var']

  def __init__(self, lhs, rhs, var=False):
    self.lhs = lhs
    self.rhs = rhs
    self.var = var


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


class if_node(node):
  __tag__ = 'if'
  __version__ = 1
  __slots__ = ['pred', 'body', 'els']

  def __init__(self, pred, body, els=None):
    self.pred = pred
    self.body = body
    self.els = els


class import_node(node):
  __tag__ = 'import'
  __version__ = 1
  __slots__ = ['name', 'rename']

  def __init__(self, name, rename=None):
    self.name = name
    self.rename = rename


class loop_node(node):
  __tag__ = 'loop'
  __version__ = 1
  __slots__ = ['body']

  def __init__(self, body):
    self.body = body


class pass_node(node):
  __tag__ = 'pass'
  __slots__ = []


class return_node(value_node):
  __tag__ = 'return'


class save_node(node):
  __tag__ = 'save'
  __version__ = 2
  __slots__ = ['value', 'name']

  def __init__(self, value, name=None):
    self.value = value
    self.name = name


class while_node(node):
  __tag__ = 'while'
  __version__ = 1
  __slots__ = ['pred', 'body']

  def __init__(self, pred, body):
    self.pred = pred
    self.body = body


# expressions

class idx_node(expr_node):
  __tag__ = 'index'
  __version__ = 1
  __slots__ = ['lhs', 'rhs']

  def __init__(self, lhs, rhs):
    self.lhs = lhs
    self.rhs = rhs


class name_node(value_node, expr_node):
  __tag__ = 'name'


class null_node(expr_node):
  __tag__ = 'null'


class int_node(value_node, expr_node):
  __tag__ = 'int'


class float_node(value_node, expr_node):
  __tag__ = 'float'


class bool_node(value_node, expr_node):
  __tag__ = 'bool'


class str_node(value_node, expr_node):
  __tag__ = 'str'


class table_node(expr_node):
  __tag__ = 'table'
  __version__ = 2


class array_node(expr_node):
  __tag__ = 'array'
  __version__ = 1
  __slots__ = ['items']

  def __init__(self, items):
    self.items = items


class dict_node(expr_node):
  __tag__ = 'dict'
  __version__ = 2
  __slots__ = ['items', 'set_meta']

  def __init__(self, items, set_meta=True):
    self.items = items
    self.set_meta = set_meta


class func_node(expr_node):
  __tag__ = 'func'
  __version__ = 3
  __slots__ = ['params', 'body']

  def __init__(self, params, body):
    self.params = params
    self.body = body


class call_node(expr_node):
  __tag__ = 'call'
  __version__ = 2
  __slots__ = ['func', 'args', 'catch', 'pop']

  def __init__(self, func, args, catch=False, pop=False):
    self.func = func
    self.args = args
    self.catch = catch
    self.pop = pop


class meth_node(expr_node):
  __tag__ = 'method'
  __version__ = 1
  __slots__ = ['lhs', 'rhs', 'args', 'catch']

  def __init__(self, lhs, rhs, args, catch=False):
    self.lhs = lhs
    self.rhs = rhs
    self.args = args
    self.catch = catch


class binary_node(expr_node):
  __tag__ = 'binary'
  __version__ = 1
  __slots__ = ['lhs', 'rhs', 'op']

  def __init__(self, lhs, rhs, op):
    self.lhs = lhs
    self.rhs = rhs
    self.op = op


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


class warning_node(node):
  __tag__ = 'warning'
  __version__ = 1
  __slots__ = ['msg']

  def __init__(self, msg):
    self.msg = msg


class hint_node(node):
  __tag__ = 'hint'
  __version__ = 1
  __slots__ = ['msg']

  def __init__(self, msg):
    self.msg = msg
