from . import ast as A
from . import emit
from . import lexer as L
from . import module as M
from . import parser as P
from . import types as T
from contextlib import contextmanager
from llvmlite import ir
from os import environ as ENV
from os import listdir as ls
from os.path import join
from termcolor import colored as C
import os.path
import subprocess
import sys
import tempfile
import traceback

compilers = {}

# USE THIS to get a new compiler. it fuzzy searches for the source file and also prevents
# multiple compilers from being made for the same file
def get_compiler(src, target=None, main=False, quiet=False):
  abspath = os.path.abspath(src)

  if abspath not in compilers:
    compilers[abspath] = Compiler(abspath, target, main, quiet)

  return compilers[abspath]


class Compiler:
  def __init__(self, file, target=None, main=False, quiet=False):
    self.file = file
    self.qname, self.mname = M.Module.find_name(file)
    self.target = target or self.mname
    self.main = main
    self.quiet = quiet
    self.lib = ENV['RAINLIB']
    self.ll = None
    self.links = None

  def print(self, msg, end='\n'):
    if not self.quiet:
      print(msg, end=end)

  @contextmanager
  def okay(self, fmt, *args):
    msg = fmt.format(*args)
    self.print('{:>10} {}...'.format(msg, C(self.qname, 'green')))
    try:
      yield
    except Exception as e:
      self.print(C('error!', 'red'))
      raise

  def goodies(self):
    # don't do this twice
    if self.links is not None:
      return

    # do everything but compile
    with self.okay('building'):
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
    self.mod = M.Module(self.file)
    self.links = set()

    builtin = get_compiler(join(ENV['RAINLIB'], '_pkg.rn'), quiet=self.quiet)

    if self is not builtin: # don't try to import builtin into builtin
      builtin.goodies()
      self.links.add(builtin.ll)

      # copy builtins into scope
      for name, val in builtin.mod.globals.items():
        self.mod[name] = val

      # add LLVM globals
      self.mod.import_from(builtin.mod)

    # compile the imports
    imports = self.ast.emit(self.mod)
    for mod in imports:
      comp = get_compiler(mod, quiet=self.quiet)
      comp.goodies() # should be done during import but might as well be safe

      # add the module's IR as well as all of its imports' IR
      self.links.add(comp.ll)
      for ll in comp.links:
        if not ll: continue
        self.links.add(ll)

    # only spit out the main if this is the main file
    if self.main:
      self.ast.emit_main(self.mod)

  def write(self):
    handle, tmp_name = tempfile.mkstemp(prefix=self.qname+'.', suffix='.ll')
    with os.fdopen(handle, 'w') as tmp:
      tmp.write(self.mod.ir)

    self.ll = tmp_name

  def compile(self):
    with self.okay('compiling'):
      core = [join(self.lib, x) for x in ls(self.lib) if x.endswith('.c')]
      clang = os.getenv('CLANG', 'clang')
      cmd = [clang, '-O2', '-o', self.target, '-lgc', '-lm', self.ll] + core + list(self.links)
      subprocess.check_call(cmd)

  def run(self):
    with self.okay('running'):
      subprocess.check_call([os.path.abspath(self.target)])
