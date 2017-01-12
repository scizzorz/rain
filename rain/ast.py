# Base classes

class metanode(type):
  def method(cls, func):
    setattr(cls, func.__name__, func)
    return func

  def __str__(self):
    return self.__name__

  def __repr__(self):
    return '<{}>'.format(self.__name__)

class node(metaclass=metanode):
  def __str__(self):
    return str(type(self))

  def __repr__(self):
    return repr(type(self))

class value_node(node):
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
  def __init__(self, stmts=[]):
    self.stmts = stmts

  def __str__(self):
    return '; '.join(str(x) for x in self.stmts)

class block_node(node):
  def __init__(self, stmts=[]):
    self.stmts = stmts

  def __str__(self):
    return '; '.join(str(x) for x in self.stmts)

# statements

class assn_node(node):
  def __init__(self, lhs, rhs, let=False):
    self.lhs = lhs
    self.rhs = rhs
    self.let = let

  def __str__(self):
    return 'assn {!s} = {!s}'.format(self.lhs, self.rhs)

class break_node(node):
  def __init__(self, cond=None):
    self.cond = cond

class cont_node(node):
  def __init__(self, cond=None):
    self.cond = cond

class if_node(node):
  def __init__(self, pred, body, els=None):
    self.pred = pred
    self.body = body
    self.els = els

  def __str__(self):
    return 'if {!s} {{ {!s} }} else {{ {!s} }}'.format(self.pred, self.body, self.els)

class loop_node(node):
  def __init__(self, body):
    self.body = body

  def __str__(self):
    return 'loop {{ {!s} }}'.format(self.body)

class pass_node(node):
  pass

class print_node(value_node):
  pass

class return_node(value_node):
  pass

class until_node(node):
  def __init__(self, pred, body):
    self.pred = pred
    self.body = body

  def __str__(self):
    return 'until {!s} {{ {!s} }}'.format(self.pred, self.body)

class while_node(node):
  def __init__(self, pred, body):
    self.pred = pred
    self.body = body

  def __str__(self):
    return 'while {!s} {{ {!s} }}'.format(self.pred, self.body)

# expressions

class idx_node(node):
  def __init__(self, lhs, rhs):
    self.lhs = lhs
    self.rhs = rhs

class name_node(value_node):
  pass

class null_node(node):
  pass

class int_node(value_node):
  pass

class float_node(value_node):
  pass

class bool_node(value_node):
  pass

class str_node(value_node):
  pass

class table_node(node):
  pass

class extern_node(node):
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return 'extern({!s})'.format(self.name)

class func_node(node):
  def __init__(self, params, body):
    self.params = params
    self.body = body

  def __str__(self):
    return 'func({!s}) {{ {!s} }}'.format(', '.join(str(x) for x in self.params), self.body)

class call_node(node):
  def __init__(self, func, args):
    self.func = func
    self.args = args

  def __str__(self):
    return '{!s}({!s})'.format(self.func, ', '.join(str(x) for x in self.args))

class meth_node(node):
  def __init__(self, lhs, rhs, args):
    self.lhs = lhs
    self.rhs = rhs
    self.args = args

  def __str__(self):
    return '{!s}:{!s}({!s})'.format(self.lhs, self.rhs, ', '.join(str(x) for x in self.args))

class is_node(node):
  def __init__(self, lhs, typ):
    self.lhs = lhs
    self.typ = typ

  def __str__(self):
    return '{!s} is {!s}'.format(self.lhs, self.typ)

class binary_node(node):
  def __init__(self, lhs, rhs, op):
    self.lhs = lhs
    self.rhs = rhs
    self.op = op

  def __str__(self):
    return '({!s} {!s} {!s})'.format(self.lhs, self.op, self.rhs)
