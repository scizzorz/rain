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

class Compiler:
  def __init__(self, src, target=None):
    self.src = src
    self.name = M.Module.find_name(src)
    self.target = target or self.name

  def goodies(self):
    self.search()
    self.read()
    self.lex()
    self.parse()
    self.emit()
    return self.write()

  def search(self):
    if os.path.isfile(self.src + '.rn'):
      self.file = self.src + '.rn'

    elif os.path.isfile(self.src):
      self.file = self.src

  def read(self):
    with open(self.file) as tmp:
      self.code = tmp.read()

  def lex(self):
    self.stream = L.stream(self.code)

  def parse(self):
    context = P.context(self.stream, file=self.file)
    self.ast = P.program(context)

  def emit(self):
    self.mod = M.Module(self.name)
    self.links = []
    imports = self.ast.emit(self.mod)

    for mod in imports:
      comp = Compiler(mod.name.value)
      self.links.append(comp.goodies())

    if 'main' in self.mod:
      self.ast.emit_main(self.mod)

  def write(self):
    handle, tmp_name = tempfile.mkstemp(prefix=self.name+'.', suffix='.ll')
    with os.fdopen(handle, 'w') as tmp:
      tmp.write(self.mod.ir)

    self.ll = tmp_name
    return self.ll

  def compile(self):
    core = [os.path.join('lib', x) for x in os.listdir('lib') if x.endswith('.c')]
    clang = os.getenv('CLANG', 'clang')
    subprocess.check_call([clang, '-O2', '-o', self.target, '-lgc', '-lm', self.ll] + core + self.links)

  def run(self):
    subprocess.check_call([self.target])
