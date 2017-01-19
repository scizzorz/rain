class metatoken(type):
  def __str__(self):
    if getattr(self, 'name', None):
      return self.name

    return self.__name__

  def __repr__(self):
    return '<{!s}>'.format(self)

class token(metaclass=metatoken):
  def __init__(self, *, line=None, col=None):
    self.line = line
    self.col = col

  def __eq__(self, other):
    return type(self) is type(other)

  def __str__(self):
    if getattr(self, 'name', None):
      return self.name
    return str(type(self))

  def __repr__(self):
    return '<{}>'.format(self)

class end_token(token):
  name = 'EOF'

# Rain

class indent_token(token):
  name = 'indent'

class dedent_token(token):
  name = 'dedent'

class newline_token(token):
  name = 'newline'

class value_token(token):
  def __init__(self, value, *, line=None, col=None):
    super().__init__(line=line, col=col)
    self.value = value

  def __eq__(self, other):
    return type(self) is other or (type(self) is type(other) and self.value == other.value)

  def __str__(self):
    if getattr(self, 'name', None):
      return '{} {!r}'.format(self.name, self.value)
    return repr(self.value)

  def __repr__(self):
    return '<{}>'.format(self)

class keyword_token(value_token):
  name = 'keyword'

class type_token(value_token):
  name = 'type'

class name_token(value_token):
  name = 'name'

class symbol_token(value_token):
  name = 'symbol'

class operator_token(value_token):
  name = 'operator'

class int_token(value_token):
  name = 'int'
  def __init__(self, value, *, line=None, col=None):
    super().__init__(int(value), line=line, col=col)

class float_token(value_token):
  name = 'float'
  def __init__(self, value, *, line=None, col=None):
    super().__init__(float(value), line=line, col=col)

class bool_token(value_token):
  name = 'bool'
  def __init__(self, value, *, line=None, col=None):
    super().__init__(value.lower() == 'true', line=line, col=col)

class string_token(value_token):
  name = 'string'
  def __init__(self, value, *, line=None, col=None):
    super().__init__(self.unescape(value), line=line, col=col)

  @staticmethod
  def unescape(data):
    return bytes(data[1:-1].encode('utf-8')).decode('unicode_escape')

class null_token(value_token):
  pass

class table_token(value_token):
  pass
