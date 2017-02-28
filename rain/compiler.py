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
c_files = {}


# USE THIS to get a new compiler. it fuzzy searches for the source file and
# also prevents multiple compilers from being made for the same file
def get_compiler(src, target=None, main=False):
  abspath = os.path.abspath(src)

  if abspath not in compilers:
    compilers[abspath] = Compiler(abspath, target, main)

  return compilers[abspath]


def compile_c(src):
  if src not in c_files:
    clang = os.getenv('CLANG', 'clang')

    handle, target = tempfile.mkstemp(prefix=os.path.basename(src), suffix='.ll')
    flags = ['-O2', '-S', '-emit-llvm']

    cmd = [clang, '-o', target, src] + flags
    subprocess.check_call(cmd)

    c_files[src] = target

  return c_files[src]


def compile_so(libs):
  # I don't know how else to find these .so files other than just asking clang
  # to make a .so file out of all of them

  clang = os.getenv('CLANG', 'clang')

  handle, target = tempfile.mkstemp(prefix='slibs', suffix='.so')
  libs = ['-l' + lib for lib in libs]

  cmd = [clang, '-shared', '-o', target] + libs
  subprocess.check_call(cmd)

  return target


def reset_compilers():
  global compilers
  global c_files
  compilers = {}
  c_files = {}


class Compiler:
  quiet = False
  verbose = False

  def __init__(self, file, target=None, main=False):
    self.file = file
    self.qname, self.mname = M.find_name(file)

    self.target = target
    self.main = main

    self.mods = OrderedSet()
    self.links = set()
    self.libs = set()

    self.stream = None  # set after lexing
    self.ast = None     # set after parsing
    self.mod = None     # set before emitting
    self.ll = None      # set after writing

    self.readen = False # read is the past tense of read, which is a method
    self.lexed = False
    self.parsed = False
    self.emitted = False
    self.built = False
    self.written = False
    self.compiled = False
    self.ran = False

  @classmethod
  def print(cls, msg, *args, end='\n'):
    if not cls.quiet:
      print(msg.format(*args), end=end)

  @classmethod
  def vprint(cls, msg, *args, end='\n'):
    if cls.verbose:
      print(msg.format(*args), end=end)

  @contextmanager
  def okay(self, tag, msg=''):
    self.print('{:>10} {}{}', tag, X(self.qname, 'green'), msg)
    try:
      yield
    except Exception as exc:
      self.print('{}: {!s}', X('error', 'red'), exc)

      if Compiler.verbose:
        traceback.print_exc()

      sys.exit(1)

  def link(self, other):
    '''Copy all of the links, libraries, and modules from another module.'''
    if other.ll:
      self.links.add(other.ll)

    self.links |= other.links
    self.libs |= other.libs
    self.mods |= other.mods

  def read(self):
    '''Read the primary source file.'''
    if self.readen:
      return
    self.readen = True

    with open(self.file) as tmp:
      self.src = tmp.read()

  def lex(self):
    '''Create a token stream from the source code.'''
    self.read()

    if self.lexed:
      return
    self.lexed = True

    self.stream = L.stream(self.src)

  def parse(self):
    '''Parse the token stream into an AST.'''
    self.lex()

    if self.parsed:
      return
    self.parsed = True

    self.parser = P.context(self.stream, file=self.file)
    self.ast = P.program(self.parser)

  def emit(self):
    '''Emit LLVM IR for the module.'''
    self.parse()

    if self.emitted:
      return
    self.emitted = True

    self.mod = M.Module(self.file)
    self.mods.add(self.mod)

    # always link with lib/_pkg.rn
    builtin = get_compiler(join(ENV['RAINLIB'], '_pkg.rn'))
    if self is not builtin:  # unless we ARE lib/_pkg.rn
      builtin.build()

      self.link(builtin)

      # import globals
      self.mod.import_scope(builtin.mod)
      self.mod.import_llvm(builtin.mod)

    # compile the imports
    imports, links, libs = self.ast.emit(self.mod)

    for mod in imports:
      comp = get_compiler(mod)
      self.vprint('           {} imports {}', X(self.qname, 'green'), X(comp.qname, 'blue'))
      comp.build()  # should be done during import but might as well be safe

      # add the module's IR as well as all of its imports' IR
      self.link(comp)
      self.mods.add(comp.mod)

    for link in links:
      self.vprint('           {} links {}', X(self.qname, 'green'), X(link, 'blue'))

    for lib in libs:
      self.vprint('           {} shares {}', X(self.qname, 'green'), X(lib, 'blue'))

    self.links |= set(links)
    self.libs |= set(libs)

    # only spit out the main if this is the main file
    if self.main:
      self.ast.emit_main(self.mod, mods=self.mods)

  def write(self):
    '''Write data based on what the latest compilation step is.'''
    if self.written:
      return
    self.written = True

    if self.built:
      handle, name = tempfile.mkstemp(prefix=self.qname + '.', suffix='.ll')
      with os.fdopen(handle, 'w') as tmp:
        tmp.write(self.mod.ir)

      self.ll = name

    elif self.emitted:
      with open(self.target or self.mname + '.ll', 'w') as tmp:
        tmp.write(self.mod.ir)

    elif self.parsed:
      with open(self.target or self.mname + '.yml', 'w') as tmp:
        tmp.write(A.machine.dump(self.ast))

    elif self.lexed:
      with open(self.target or self.mname + '.lex', 'w') as tmp:
        for token in self.stream:
          tmp.write(str(token))
          tmp.write('\n')

  def build(self):
    '''Emit code and write it to a file.'''
    if self.built:
      return
    self.built = True

    msg = ''
    if Compiler.verbose:
      msg = ' from {}'.format(X(self.file, 'blue'))

    with self.okay('building', msg=msg):
      self.emit()
      self.write()

  def compile_links(self):
    '''Compile all additional link files into LLVM IR.'''
    drop = set()
    add = set()

    for link in self.links:
      if link.endswith('.ll') or link.endswith('.so'):
        continue

      target = compile_c(link)

      drop.add(link)
      add.add(target)

    self.links = (self.links | add) - drop

    return compile_so(self.libs)

  def compile(self):
    '''Compile a full program into an executable.'''
    self.build()

    if self.compiled:
      return
    self.compiled = True

    self.compile_links()

    with self.okay('compiling'):
      target = self.target or self.mname
      clang = os.getenv('CLANG', 'clang')
      flags = ['-O2']
      libs = ['-l' + lib for lib in self.libs]
      cmd = [clang, '-o', target, self.ll] + flags + libs + list(self.links)

      self.vprint('{:>10} {}', 'target', X(target, 'yellow'))
      self.vprint('{:>10} {}', 'flags', X('  '.join(flags), 'yellow'))
      self.vprint('{:>10} {}', 'main', X(self.ll, 'yellow'))
      for link in self.links:
        self.vprint('{:>10} {}', 'link', X(link, 'yellow'))

      for lib in libs:
        self.vprint('{:>10} {}', 'lib', X(lib, 'yellow'))

      subprocess.check_call(cmd)

  def share(self):
    '''Compile a single Rain file into a shared object file.'''
    self.build()

    if self.compiled:
      return
    self.compiled = True

    self.compile_links()

    with self.okay('sharing'):
      target = self.target or self.mname + '.so'
      clang = os.getenv('CLANG', 'clang')
      flags = ['-O2', '-shared', '-fPIC']
      cmd = [clang, '-o', target, self.ll] + flags

      self.vprint('{:>10} {}', 'target', X(target, 'yellow'))
      self.vprint('{:>10} {}', 'flags', X('  '.join(flags), 'yellow'))
      self.vprint('{:>10} {}', 'src', X(self.ll, 'yellow'))

      subprocess.check_call(cmd)

  def run(self):
    '''Execute a generated executable.'''
    with self.okay('running'):
      target = self.target or self.mname
      subprocess.check_call([os.path.abspath(target)])
