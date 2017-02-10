import rain.lexer as L
import rain.token as K
import pytest

def test_factory():
  assert L.factory('return') == K.keyword_token('return')
  assert L.factory('this') == K.name_token('this')
  assert L.factory('Multi_Word') == K.name_token('multiword')

def test_keywords():
  stream = L.stream(' '.join(L.KEYWORDS))
  for token, keyword in zip(stream, L.KEYWORDS):
    assert token == K.keyword_token(keyword)

def test_operators():
  stream = L.stream(' '.join(L.KW_OPERATORS))
  for token, keyword in zip(stream, L.KW_OPERATORS):
    assert token == K.operator_token(keyword)

  stream = L.stream(' '.join(L.OPERATORS))
  for token, keyword in zip(stream, L.OPERATORS):
    assert token == K.operator_token(keyword)

def test_literals():
  stream = L.stream('0 10 0.0 0.1 0.12 1.23 12.34 true false "string" "escaped \\"string\\"" null table')

  assert next(stream) == K.int_token(0)
  assert next(stream) == K.int_token(10)
  assert next(stream) == K.float_token(0.0)
  assert next(stream) == K.float_token(0.1)
  assert next(stream) == K.float_token(0.12)
  assert next(stream) == K.float_token(1.23)
  assert next(stream) == K.float_token(12.34)
  assert next(stream) == K.bool_token('true')
  assert next(stream) == K.bool_token('false')
  assert next(stream) == K.string_token('"string"')
  assert next(stream) == K.string_token('"escaped \\"string\\""')
  assert next(stream) == K.null_token('null')
  assert next(stream) == K.table_token('table')
  assert next(stream) == K.end_token()

def test_whitespace():
  stream = L.stream('1\n'
                    '\n'        # extra blank lines
                    ' \n'
                    '2\n'
                    '  3\n'     # indent
                    '\n'        # blank lines in a block
                    '\n'
                    '  4\n'
                    '    5  \n'
                    '\n'        # all sorts of whitespace
                    ' \n'
                    '  \n'
                    '   \n'
                    '    \n'
                    '    6  \n' # trailing whitespace
                    '  7\n'     # dedent
                    '      8\n'
                    '9\n'       # multiple simultaneous dedents
                    ' 10\n'
                    '  11\n')   # ending dedent

  assert next(stream) == K.int_token(1)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.int_token(2)
  assert next(stream) == K.indent_token()
  assert next(stream) == K.int_token(3)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.int_token(4)
  assert next(stream) == K.indent_token()
  assert next(stream) == K.int_token(5)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.int_token(6)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.dedent_token()
  assert next(stream) == K.newline_token()
  assert next(stream) == K.int_token(7)
  assert next(stream) == K.indent_token()
  assert next(stream) == K.int_token(8)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.dedent_token()
  assert next(stream) == K.newline_token()
  assert next(stream) == K.dedent_token()
  assert next(stream) == K.newline_token()
  assert next(stream) == K.int_token(9)
  assert next(stream) == K.indent_token()
  assert next(stream) == K.int_token(10)
  assert next(stream) == K.indent_token()
  assert next(stream) == K.int_token(11)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.dedent_token()
  assert next(stream) == K.newline_token()
  assert next(stream) == K.dedent_token()
  assert next(stream) == K.newline_token()
  assert next(stream) == K.end_token()

def test_comments():
  stream = L.stream('# full line\n'
                    '1 # end of line\n'
                    '2 # end of line\n'
                    '  3 # end of line\n'
                    '# end of block\n'
                    '4 # end of line\n'
                    '# end of program')

  assert next(stream) == K.int_token(1)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.int_token(2)
  assert next(stream) == K.indent_token()
  assert next(stream) == K.int_token(3)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.dedent_token()
  assert next(stream) == K.newline_token()
  assert next(stream) == K.int_token(4)
  assert next(stream) == K.newline_token()
  assert next(stream) == K.end_token()

def test_prints():
  assert str(K.end_token) == 'EOF'
  assert repr(K.end_token) == '<EOF>'
  assert str(K.end_token()) == 'EOF'
  assert repr(K.end_token()) == '<EOF>'
  assert str(K.int_token(5)) == 'int 5'
  assert repr(K.int_token(5)) == '<int 5>'
