from . import ast as A
from . import emit
from . import lexer as L
from . import module as M
from . import parser as P
from . import types as T
from contextlib import contextmanager
from enum import Enum
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
def get_compiler(src, target=None, main=False):
  abspath = os.path.abspath(src)

  if abspath not in compilers:
    compilers[abspath] = Compiler(abspath, target, main)

  return compilers[abspath]

def reset_compilers():
  global compilers
  compilers = {}

class phases(Enum):
  lexing = 0
  parsing = 1
  emitting = 2
  building = 3

class Compiler:
  quiet = False

  def __init__(self, file, target=None, main=False):
    self.file = file
    self.qname, self.mname = M.find_name(file)
    self.target = target
    self.main = main
    self.lib = ENV['RAINLIB']
    self.links = set()
    self.stream = None # set after lexing
    self.ast = None    # set after parsing
    self.mod = None    # set before emitting
    self.ll = None     # set after writing

  @classmethod
  def print(cls, msg, end='\n'):
    if not cls.quiet:
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

  def goodies(self, phase=phases.building):
    # don't do this twice
    if self.mod is not None:
      return

    # do everything but compile
    with self.okay(phase.name):
      self.read()
      self.lex()

      if phase.value > phases.lexing.value:
        self.parse()
      if phase.value > phases.parsing.value:
        self.emit()

      self.write(phase)

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

    # always link with lib/_pkg.rn
    builtin = get_compiler(join(ENV['RAINLIB'], '_pkg.rn'))
    if self is not builtin: # unless we ARE lib/_pkg.rn
      builtin.goodies()

      self.links.add(builtin.ll)
      for link in builtin.links:
        if not link: continue
        self.links.add(link)

      # copy builtins into scope
      for name, val in builtin.mod.globals.items():
        self.mod[name] = val

      # import LLVM globals
      self.mod.import_from(builtin.mod)

    # compile the imports
    imports, links = self.ast.emit(self.mod)
    for mod in imports:
      comp = get_compiler(mod)
      comp.goodies() # should be done during import but might as well be safe

      # add the module's IR as well as all of its imports' IR
      self.links.add(comp.ll)
      for link in comp.links:
        if not link: continue
        self.links.add(link)

    # add the links
    for link in links:
      if not link: continue
      self.links.add(link)

    # only spit out the main if this is the main file
    if self.main:
      self.ast.emit_main(self.mod)

  def write(self, phase=phases.building):
    if phase == phases.lexing:
      with open(self.target or self.mname + '.lex', 'w') as tmp:
        for token in self.stream:
          tmp.write(str(token))
          tmp.write('\n')

    elif phase == phases.parsing:
      with open(self.target or self.mname + '.yml', 'w') as tmp:
        tmp.write(A.machine.dump(self.ast))

    elif phase == phases.emitting:
      with open(self.target or self.mname + '.ll', 'w') as tmp:
        tmp.write(self.mod.ir)

    elif phase == phases.building:
      handle, tmp_name = tempfile.mkstemp(prefix=self.qname+'.', suffix='.ll')
      with os.fdopen(handle, 'w') as tmp:
        tmp.write(self.mod.ir)

      self.ll = tmp_name

  def compile(self):
    with self.okay('compiling'):
      target = self.target or self.mname
      clang = os.getenv('CLANG', 'clang')
      cmd = [clang, '-O2', '-o', target, '-lgc', '-lm', self.ll] + list(self.links)
      subprocess.check_call(cmd)

  def run(self):
    with self.okay('running'):
      target = self.target or self.mname
      subprocess.check_call([os.path.abspath(target)])
