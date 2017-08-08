from . import ast as A
from . import token as K
from contextlib import contextmanager
import rvmpy
from os.path import isdir, isfile
from os.path import join
import os.path
import re

name_chars = re.compile('[^a-z0-9]')

TRACE_MAIN = -1
TRACE_INIT = -2
TRACE_UNKNOWN = -3


# get default paths
def get_paths():
  path = os.environ['RAINPATH'].split(':') if 'RAINPATH' in os.environ else []
  core = [os.environ['RAINBASE'], os.environ['RAINLIB']]
  return path + core


# normalize a name - remove all special characters and cases
def normalize_name(name):
  return name_chars.sub('', name.lower())


# find a rain file from a module identifier
def find_rain(src, paths=[]):
  if src[0] == '/':
    paths = ['']
  elif src[0] != '.':
    paths = get_paths() + paths

  for path in paths:
    if isfile(join(path, src) + '.rn'):
      return join(path, src) + '.rn'
    elif isfile(join(path, src)) and src.endswith('.rn'):
      return join(path, src)
    elif isdir(join(path, src)) and isfile(join(path, src, '_pkg.rn')):
      return join(path, src, '_pkg.rn')


# find any file from a string
def find_file(src, paths=[]):
  if src[0] == '/':
    paths = ['']
  elif src[0] != '.':
    paths = paths + get_paths()

  for path in paths:
    if os.path.isfile(join(path, src)):
      return join(path, src)


# find a module name
def find_name(src):
  path = os.path.abspath(src)
  path, name = os.path.split(path)
  fname, ext = os.path.splitext(name)

  if fname == '_pkg':
    _, fname = os.path.split(path)

  mname = normalize_name(fname)

  proot = []
  while path and os.path.isfile(join(path, '_pkg.rn')):
    path, name = os.path.split(path)
    proot.insert(0, normalize_name(name))

  if not src.endswith('_pkg.rn'):
    proot.append(mname)

  qname = '.'.join(proot)

  return (qname, mname)


class Module:
  def __init__(self, file=None, name=None):
    if name:
      self.qname = self.mname = name
    else:
      self.file = file
      self.qname, self.mname = find_name(self.file)

    self.rvm = rvmpy.Module(name=self.qname)

    self.builder = None
    self.arg_ptrs = None
    self.landingpad = None
    self.before = None
    self.loop = None
    self.after = None
    self.ret_ptr = None
    self.bind_ptr = None
    self.bindings = None

    self.name_counter = 0

  def __str__(self):
    return 'Module {!r}'.format(self.qname)

  def __repr__(self):
    return '<{!s}>'.format(self)

  # save and restore some module attributes around a code block
  @contextmanager
  def stack(self, *attrs):
    saved = [getattr(self, attr) for attr in attrs]
    yield
    for attr, val in zip(attrs, saved):
      setattr(self, attr, val)
