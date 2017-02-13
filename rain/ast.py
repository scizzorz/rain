import camel
import fixedint
import struct

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
    return '<{}>'.format(self.__name__)


class node(metaclass=metanode):
  __tag__ = 'node'
  __version__ = 1
  __slots__ = []


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
  pass


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
  __version__ = 2
  __slots__ = ['lhs', 'rhs', 'let', 'export']

  def __init__(self, lhs, rhs, let=False, export=False):
    self.lhs = lhs
    self.rhs = rhs
    self.let = let
    self.export = export


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


class export_foreign_node(node):
  __tag__ = 'export_foreign'
  __version__ = 1
  __slots__ = ['name', 'rename']

  def __init__(self, name, rename):
    self.name = name
    self.rename = rename


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


class link_node(node):
  __tag__ = 'link'
  __version__ = 1
  __slots__ = ['name']

  def __init__(self, name):
    self.name = name


class lib_node(node):
  __tag__ = 'library'
  __version__ = 1
  __slots__ = ['name']

  def __init__(self, name):
    self.name = name


class loop_node(node):
  __tag__ = 'loop'
  __version__ = 1
  __slots__ = ['body']

  def __init__(self, body):
    self.body = body


class macro_node(node):
  __tag__ = 'macro'
  __version__ = 1
  __slots__ = ['name', 'types', 'params', 'body']

  def __init__(self, name, types, params, body):
    self.name = name
    self.types = types
    self.params = params
    self.body = body

class pass_node(node):
  __tag__ = 'pass'


class return_node(value_node):
  __tag__ = 'return'


class save_node(value_node):
  __tag__ = 'save'


class until_node(node):
  __tag__ = 'until'
  __version__ = 1
  __slots__ = ['pred', 'body']

  def __init__(self, pred, body):
    self.pred = pred
    self.body = body


class while_node(node):
  __tag__ = 'while'
  __version__ = 1
  __slots__ = ['pred', 'body']

  def __init__(self, pred, body):
    self.pred = pred
    self.body = body


class for_node(node):
  __tag__ = 'for'
  __version__ = 1
  __slots__ = ['name', 'func', 'body']

  def __init__(self, name, func, body):
    self.name = name
    self.func = func
    self.body = body


class with_node(node):
  __tag__ = 'with'
  __version__ = 1
  __slots__ = ['expr', 'params', 'body']

  def __init__(self, expr, params, body):
    self.expr = expr
    self.params = params
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


class literal_node(expr_node):
  def hash(self):
    raise Exception("Can't hash {!s}".format(self))


class null_node(literal_node):
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
    raw = struct.pack('d', self.value)
    return struct.unpack('Q', raw)[0]


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


class table_node(expr_node):
  __tag__ = 'table'
  __version__ = 1
  __slots__ = ['parent']

  def __init__(self, parent=None):
    self.parent = parent


class func_node(expr_node):
  __tag__ = 'func'
  __version__ = 1
  __slots__ = ['params', 'body']

  def __init__(self, params, body):
    self.params = params
    self.body = body


class foreign_node(expr_node):
  __tag__ = 'foreign'
  __version__ = 1
  __slots__ = ['name', 'params']

  def __init__(self, name, params):
    self.name = name
    self.params = params


class call_node(expr_node):
  __tag__ = 'call'
  __version__ = 1
  __slots__ = ['func', 'args', 'catch']

  def __init__(self, func, args, catch=False):
    self.func = func
    self.args = args
    self.catch = catch


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
