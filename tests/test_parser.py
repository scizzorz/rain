import pytest
import rain.ast as A
import rain.lexer as L
import rain.parser as P
import utils

TEST_DIR = 'tests/parse'

@pytest.mark.parametrize('src', utils.lsrn('tests/parse'))
def test_parse(src):
  with open(src + '.yml') as fp:
    target = fp.read()

  output = utils.parse(src)

  assert output == target
