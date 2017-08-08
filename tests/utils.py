import os
import rain.ast as A
import rain.lexer as L
import rain.parser as P

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

def parse(src):
  with open(src) as fp:
    code = fp.read()

  stream = L.stream(code)
  parser = P.context(stream, file=src)
  ast = P.program(parser)

  return A.machine.dump(ast)
