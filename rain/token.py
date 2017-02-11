class coord:
  def __init__(self, line=0, col=0, file=None):
    self.line = line
    self.col = col
    self.file = file

  def __str__(self):
    ret = ''
    if self.file:
      ret += self.file + ':'

    if self.line and self.col:
      ret += str(self.line) + ':' + str(self.col) + ':'
    elif self.line:
      ret += str(self.line) + ':'

    return ret

  def __repr__(self):
    return '<{!s}>'.format(self)

class metatoken(type):
  def __str__(self):
    if getattr(self, 'name', None):
      return self.name

    return self.__name__

  def __repr__(self):
    return '<{!s}>'.format(self)


class token(metaclass=metatoken):
  def __init__(self, *, pos=coord()):
    self.pos = pos

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
  def __init__(self, value, *, pos=coord()):
    super().__init__(pos=pos)
    self.value = value

  def __eq__(self, other):
    typ = type(self) is other
    val = type(self) is type(other) and self.value == other.value
    return typ or val

  def __str__(self):
    if getattr(self, 'name', None):
      return '{} {!r}'.format(self.name, self.value)
    return repr(self.value)

  def __repr__(self):
    return '<{}>'.format(self)


class keyword_token(value_token):
  name = 'keyword'


class name_token(value_token):
  name = 'name'


class symbol_token(value_token):
  name = 'symbol'


class operator_token(value_token):
  name = 'operator'


class int_token(value_token):
  name = 'int'

  def __init__(self, value, *, pos=coord()):
    super().__init__(int(value), pos=pos)


class float_token(value_token):
  name = 'float'

  def __init__(self, value, *, pos=coord()):
    super().__init__(float(value), pos=pos)


class bool_token(value_token):
  name = 'bool'

  def __init__(self, value, *, pos=coord()):
    super().__init__(value.lower() == 'true', pos=pos)


class string_token(value_token):
  name = 'string'

  def __init__(self, value, *, pos=coord()):
    super().__init__(self.unescape(value), pos=pos)

  @staticmethod
  def unescape(data):
    return bytes(data[1:-1].encode('utf-8')).decode('unicode_escape')


class null_token(value_token):
  pass


class table_token(value_token):
  pass
