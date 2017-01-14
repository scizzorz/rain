import os.path
import pytest
import rain.compiler as C

def ls(*path):
  path = os.path.join(*path)
  for file in os.listdir(path):
    yield os.path.join(path, file)

def lsrn(*path, recurse=False):
  for file in ls(*path):
    if os.path.isfile(file) and file.endswith('.rn') and not file.endswith('_pkg.rn'):
      yield file
    elif recurse and os.path.isdir(file):
      yield from lsrn(file, recurse=recurse)

@pytest.mark.parametrize('src', lsrn('samples', recurse=True))
def test_sample(src):
  comp = C.get_compiler(src, main=True, quiet=True)
  comp.goodies()
  comp.compile()
