import os
import os.path
import subprocess
import pytest
import rain.compiler as C

os.putenv('RAIN_TEST', 'testing') # for command line args test

C.Compiler.quiet = True

def ls(*path):
  '''List all files in a directory.'''

  path = os.path.join(*path)
  for file in os.listdir(path):
    yield os.path.join(path, file)

def lsrn(*path, recurse=False):
  '''List all *.rn files in a direcotry.'''

  for file in ls(*path):
    if os.path.isfile(file) and file.endswith('.rn') and not file.endswith('_pkg.rn'):
      yield file
    elif recurse and os.path.isdir(file):
      yield from lsrn(file, recurse=recurse)

def check_file(name):
  '''Check for the correct output file in tests/outputs/ and then compare the file contents.'''

  correct = os.path.join('tests', 'outputs', name)
  assert os.path.isfile(correct)
  with open(name) as out, open(correct) as exp:
    assert out.read() == exp.read()

@pytest.mark.parametrize('src', lsrn('samples', recurse=True))
def test_lex(src):
  '''Test the lexing phase.'''

  comp = C.get_compiler(src, main=True)
  comp.target = comp.mname + '.lex'
  comp.goodies(C.phases.lexing)

  check_file(comp.target)
  os.remove(comp.target)

@pytest.mark.parametrize('src', lsrn('samples', recurse=True))
def test_parse(src):
  '''Test the parsing phase.'''

  comp = C.get_compiler(src, main=True)
  comp.target = comp.mname + '.yml'
  comp.goodies(C.phases.parsing)

  check_file(comp.target)
  os.remove(comp.target)

@pytest.mark.parametrize('src', lsrn('samples', recurse=True))
def test_compile(src):
  '''Test the compilation phase.'''

  comp = C.get_compiler(src, main=True)
  comp.target = comp.mname
  comp.goodies(C.phases.building)
  comp.compile()
  os.remove(comp.target)

@pytest.mark.parametrize('src', lsrn('samples', recurse=True))
def test_run(src):
  '''Test program execution and results.'''

  comp = C.get_compiler(src, main=True)
  comp.target = comp.mname
  comp.goodies(C.phases.building)
  comp.compile()

  with open(comp.target + '.out', 'w') as tmp:
    subprocess.call([comp.target], stdout=tmp)

  check_file(comp.target + '.out')
  os.remove(comp.target + '.out')
  os.remove(comp.target)
