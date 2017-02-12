from . import ast as A
from . import emit
from . import lexer as L
from . import module as M
from . import parser as P
from contextlib import contextmanager
from enum import Enum
from orderedset import OrderedSet
from os import environ as ENV
from os.path import join
from termcolor import colored as X
import os.path
import subprocess
import sys
import tempfile
import traceback

compilers = {}


# USE THIS to get a new compiler. it fuzzy searches for the source file and
# also prevents multiple compilers from being made for the same file
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
  NONE  = 0
  READ  = 1
  LEX   = 2
  PARSE = 3
  EMIT  = 4
  WRITE = 5
  COMP  = 6

  quiet = False
  verbose = False

  def __init__(self, file, target=None, main=False):
    self.file = file
    self.qname, self.mname = M.find_name(file)

    if Compiler.verbose:
      self.print('{:>10} {} from {}', 'using', X(self.qname, 'green'), X(self.file, 'blue'))

    self.target = target
    self.main = main

    self.mods = OrderedSet()
    self.links = set()
    self.libs = set()

    self.phase = Compiler.NONE
    self.stream = None  # set after lexing
    self.ast = None     # set after parsing
    self.mod = None     # set before emitting
    self.ll = None      # set after writing

  @classmethod
  def print(cls, msg, *args, end='\n'):
    if not cls.quiet:
      print(msg.format(*args), end=end)

  @contextmanager
  def okay(self, fmt, *args):
    msg = fmt.format(*args)
    self.print('{:>10} {}', msg, X(self.qname, 'green'))
    try:
      yield
    except Exception as exc:
      self.print('{}: {!s}', X('error', 'red'), exc)

      if Compiler.verbose:
        traceback.print_exc()

      sys.exit(1)

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
    if self.phase >= Compiler.READ:
      return
    self.phase = Compiler.READ

    with open(self.file) as tmp:
      self.src = tmp.read()

  def lex(self):
    if self.phase >= Compiler.LEX:
      return
    self.phase = Compiler.LEX

    self.stream = L.stream(self.src)

  def parse(self):
    if self.phase >= Compiler.PARSE:
      return
    self.phase = Compiler.PARSE

    self.parser = P.context(self.stream, file=self.file)
    self.ast = P.program(self.parser)

  def link(self, other):
    if other.ll:
      self.links.add(other.ll)

    self.links |= other.links
    self.libs |= other.libs
    self.mods |= other.mods

  def emit(self):
    if self.phase >= Compiler.EMIT:
      return
    self.phase = Compiler.EMIT

    self.mod = M.Module(self.file)
    self.mods.add(self.mod)

    # always link with lib/_pkg.rn
    builtin = get_compiler(join(ENV['RAINLIB'], '_pkg.rn'))
    if self is not builtin:  # unless we ARE lib/_pkg.rn
      builtin.goodies()

      self.link(builtin)

      # copy builtins into scope
      for name, val in builtin.mod.globals.items():
        self.mod[name] = val

      # import LLVM globals
      self.mod.import_from(builtin.mod)

    # compile the imports
    imports, links, libs = self.ast.emit(self.mod)
    for mod in imports:
      comp = get_compiler(mod)
      comp.goodies()  # should be done during import but might as well be safe

      # add the module's IR as well as all of its imports' IR
      self.link(comp)

    self.mods |= OrderedSet(get_compiler(mod).mod for mod in imports)
    self.links |= set(links)
    self.libs |= set(libs)

    if Compiler.verbose:
      for link in links:
        self.print('{:>10} {}', 'linking', X(link, 'blue'))

      for lib in libs:
        self.print('{:>10} {}', 'sharing', X(lib, 'blue'))

    # only spit out the main if this is the main file
    if self.main:
      self.ast.emit_main(self.mod, mods=self.mods)

  def write(self, phase=phases.building):
    if self.phase >= Compiler.WRITE:
      return
    self.phase = Compiler.WRITE

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
      handle, name = tempfile.mkstemp(prefix=self.qname + '.', suffix='.ll')
      with os.fdopen(handle, 'w') as tmp:
        tmp.write(self.mod.ir)

      self.ll = name

  def compile_links(self):
    clang = os.getenv('CLANG', 'clang')
    drop = set()
    add = set()

    for link in self.links:
      if link.endswith('.ll'):
        continue

      handle, target = tempfile.mkstemp(prefix=os.path.basename(link), suffix='.ll')
      flags = ['-O2', '-S', '-emit-llvm']
      cmd = [clang, '-o', target, link] + flags
      subprocess.check_call(cmd)

      drop.add(link)
      add.add(target)

    self.links = (self.links | add) - drop

    # compile shared libraries too!
    handle, target = tempfile.mkstemp(prefix='slibs', suffix='.so')
    libs = ['-l' + lib for lib in self.libs]
    cmd = [clang, '-shared', '-o', target] + libs
    subprocess.check_call(cmd)
    return target

  def compile(self):
    if self.phase >= Compiler.COMP:
      return
    self.phase = Compiler.COMP

    with self.okay('compiling'):
      target = self.target or self.mname
      clang = os.getenv('CLANG', 'clang')
      flags = ['-O2']
      libs = ['-l' + lib for lib in self.libs]
      cmd = [clang, '-o', target, self.ll] + flags + libs + list(self.links)
      subprocess.check_call(cmd)

  def run(self):
    with self.okay('running'):
      target = self.target or self.mname
      subprocess.check_call([os.path.abspath(target)])
