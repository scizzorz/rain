from . import ast as A
from . import error as Q
from . import lexer as L
from . import module as M
from . import parser as P
from contextlib import contextmanager
from orderedset import OrderedSet
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

    self.stream = None  # set after lexing
    self.ast = None     # set after parsing
    self.mod = None     # set before emitting
    self.ll = None      # set after writing

    self.readen = False  # read is the past tense of read, which is a method...
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
    '''Emit RVM bytecode for the module.'''
    self.parse()

    if self.emitted:
      return
    self.emitted = True

    self.mod = M.Module(self.file)

    # compile the imports
    self.ast.emit(self.mod)

  def write(self):
    '''Write data based on what the latest compilation step is.'''
    if self.written:
      return
    self.written = True

    if self.emitted:
      with open(self.target or self.qname + '.rnc', 'wb') as tmp:
        self.mod.write(tmp)

    elif self.parsed:
      with open(self.target or self.qname + '.yml', 'w') as tmp:
        tmp.write(A.machine.dump(self.ast))

    elif self.lexed:
      with open(self.target or self.qname + '.lex', 'w') as tmp:
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

  def compile(self):
    '''Compile a full program into an executable.'''
    self.build()

    if self.compiled:
      return
    self.compiled = True

  def run(self):
    '''Execute a generated executable.'''
    with self.okay('running'):
      pass
