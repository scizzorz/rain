class metatoken(type):
  def __str__(self):
    return self.__name__

  def __repr__(self):
    return '<{}>'.format(self.__name__)

class token(metaclass=metatoken):
  def __init__(self, *, line=None, col=None):
    self.line = line
    self.col = col

  def __eq__(self, other):
    return type(self) is type(other)

  def __str__(self):
    return str(type(self))

  def __repr__(self):
    return '<{}>'.format(self)

class end_token(token):
  pass

# Rain

class indent_token(token):
  pass

class dedent_token(token):
  pass

class newline_token(token):
  pass

class value_token(token):
  def __init__(self, value, *, line=None, col=None):
    super().__init__(line=line, col=col)
    self.value = value

  def __eq__(self, other):
    return type(self) is other or (type(self) is type(other) and self.value == other.value)

  def __str__(self):
    return '{}({!r})'.format(type(self), self.value)

  def __repr__(self):
    return '<{}>'.format(self)

class keyword_token(value_token):
  pass

class type_token(value_token):
  pass

class name_token(value_token):
  pass

class symbol_token(value_token):
  pass

class operator_token(value_token):
  pass

class int_token(value_token):
  def __init__(self, value, *, line=None, col=None):
    super().__init__(int(value), line=line, col=col)

class float_token(value_token):
  def __init__(self, value, *, line=None, col=None):
    super().__init__(float(value), line=line, col=col)

class bool_token(value_token):
  def __init__(self, value, *, line=None, col=None):
    super().__init__(value.lower() == 'true', line=line, col=col)

class string_token(value_token):
  def __init__(self, value, *, line=None, col=None):
    super().__init__(self.unescape(value), line=line, col=col)

  @staticmethod
  def unescape(data):
    return bytes(data[1:-1].encode('utf-8')).decode('unicode_escape')

class null_token(value_token):
  pass

class table_token(value_token):
  pass
