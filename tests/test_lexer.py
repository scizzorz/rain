import pytest
import rain.lexer as L
import rain.token as K

def stream_test(typ, ls):
  def wrapper(fn):
    @pytest.mark.parametrize('src', ls)
    def inner(src):
      stream = L.stream(src)
      assert next(stream) == typ(src)
      assert next(stream) == K.end_token()

    return inner

  return wrapper

def test_factory():
  assert L.factory('return') == K.keyword_token('return')
  assert L.factory('this') == K.name_token('this')
  assert L.factory('Multi_Word') == K.name_token('multiword')


@stream_test(K.keyword_token, L.KEYWORDS)
def test_keywords(src):
  pass

@stream_test(K.operator_token, L.KW_OPERATORS + L.OPERATORS)
def test_operators(src):
  pass


@stream_test(K.float_token, ['0.0', '0.1', '0.12', '0.123', '12.34'])
def test_floats(src):
  pass


@stream_test(K.int_token, ['0', '1', '10'])
def test_ints(src):
  pass


@stream_test(K.bool_token, ['true', 'false'])
def test_bools(src):
  pass


@stream_test(K.string_token, ['"string"', r'"\"escaped string\""', r'"before \"escape\""', r'"\"after\" escape"'])
def test_strings(src):
  pass


@stream_test(K.null_token, ['null'])
def test_null(src):
  pass


@stream_test(K.table_token, ['table'])
def test_table(src):
  pass


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
