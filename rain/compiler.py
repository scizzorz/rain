import os.path
import subprocess
import sys
import tempfile
import traceback

from . import ast as A
from . import emit
from . import lexer as L
from . import module as M
from . import parser as P
from . import types as T
from termcolor import colored as C

compilers = {}

# USE THIS to get a new compiler. it fuzzy searches for the source file and also prevents
# multiple compilers from being made for the same file
def get_compiler(src, target=None, main=False):
  if os.path.isfile(src + '.rn'):
    file = src + '.rn'

  elif os.path.isfile(src):
    file = src

  abspath = os.path.abspath(file)

  if abspath not in compilers:
    compilers[abspath] = Compiler(file, target, main)

  return compilers[abspath]


class Compiler:
  def __init__(self, file, target=None, main=False):
    self.file = file
    self.name = M.Module.find_name(file)
    self.target = target or self.name
    self.main = main
    self.ll = None
    self.links = None

  def goodies(self):
    # do everything but compile
    self.read()
    self.lex()
    self.parse()
    self.emit()
    self.write()

  def read(self):
    with open(self.file) as tmp:
      self.src = tmp.read()

  def lex(self):
    self.stream = L.stream(self.src)

  def parse(self):
    context = P.context(self.stream, file=self.file)
    self.ast = P.program(context)

  def emit(self):
    self.mod = M.Module(self.name)
    imports = self.ast.emit(self.mod)
    self.links = []

    for mod in imports:
      comp = get_compiler(mod.name.value)
      # comp.links is set to [] after code generation
      # so if it's already non-None, then we don't need to regenerate code, but do need to link
      if comp.links is None:
        comp.goodies()

      self.links.append(comp.ll)

    # only spit out the main if this is the main file
    if self.main:
      self.ast.emit_main(self.mod)

  def write(self):
    handle, tmp_name = tempfile.mkstemp(prefix=self.name+'.', suffix='.ll')
    with os.fdopen(handle, 'w') as tmp:
      tmp.write(self.mod.ir)

    self.ll = tmp_name

  def compile(self):
    core = [os.path.join('lib', x) for x in os.listdir('lib') if x.endswith('.c')]
    clang = os.getenv('CLANG', 'clang')
    subprocess.check_call([clang, '-O2', '-o', self.target, '-lgc', '-lm', self.ll] + core + self.links)

  def run(self):
    subprocess.check_call([self.target])
