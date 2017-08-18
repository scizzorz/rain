from . import instr as I
from contextlib import contextmanager
from os.path import isdir, isfile
from os.path import join
import ctypes as ct
import os.path
import re
import struct


name_chars = re.compile('[^a-z0-9]')


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


class Box(ct.Structure):
  null = 0
  int = 1
  float = 2
  bool = 3
  str = 4
  table = 5
  func = 6
  cdata = 7

  _saves_ = []

  # strings should be saved on Module, not Box
  # right now, every Module produced writes the whole set of strings
  _strings_ = []

  def __str__(self):
    env_p = ct.cast(self.env, ct.c_void_p).value or 0
    return 'Box({}, {}, 0x{:08x}, 0x{:08x})'.format(self.type, self.size, self.data, env_p)

  def __repr__(self):
    return '<{!s}>'.format(self)

  @classmethod
  def new(cls, *args, **kwargs):
    obj = cls(*args, **kwargs)
    cls._saves_.append(obj)
    return obj

  @classmethod
  def to_rain(cls, val):
    if val is None:
      return cls.new(cls.null, 0, 0, cls.nullptr)

    elif val is False:
      return cls.new(cls.bool, 0, 0, cls.nullptr)

    elif val is True:
      return cls.new(cls.bool, 0, 1, cls.nullptr)

    elif isinstance(val, int):
      return cls.new(cls.int, 0, val, cls.nullptr)

    elif isinstance(val, float):
      raw = struct.pack('d', val)
      intrep = struct.unpack('Q', raw)[0]
      return cls.new(cls.float, 0, intrep, cls.nullptr)

    elif isinstance(val, str):
      idx = len(cls._strings_)
      cls._strings_.append(val)
      return cls.new(cls.str, len(val), idx, cls.nullptr)

    elif isinstance(val, type(lambda: 0)):
      return cls.new(cls.func, 0, val(), cls.nullptr)

    raise Exception("Can't convert value {!r} to Rain".format(val))


Box._fields_ = [('type', ct.c_uint8),
                ('size', ct.c_uint32),
                ('data', ct.c_uint64),
                ('env', ct.POINTER(Box))]
Box.nullptr = ct.POINTER(Box)()


class Block:
  def __init__(self):
    self.addr = None
    self.instrs = []

  def __len__(self):
    return len(self.instrs)

  def write(self, fp):
    for instr in self.instrs:
      fp.write(instr.as_c())

  def add_instr(self, *instrs):
    self.instrs.extend(instrs)

  def set_addr(self, addr):
    self.addr = addr

  def finalize(self):
    self.instrs = tuple(self.instrs)

    for i, instr in enumerate(self.instrs):
      if isinstance(instr, I.CallTo):
        instr.x = instr.block.addr

      elif isinstance(instr, (I.Jump, I.JumpIf, I.JumpNe)):
        instr.x = instr.block.addr - (self.addr + i) - 1


class Module:
  def __init__(self, file=None, name=None):
    if name:
      self.qname = self.mname = name
    else:
      self.file = file
      self.qname, self.mname = find_name(self.file)

    self.consts = []
    self.block = None
    self.main = Block()
    self.blocks = [self.main]
    self.frozen = False
    self.instr_count = 0

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

  def finalize(self):
    # hacky, but works for now
    self.blocks = tuple(self.blocks)
    self.consts = tuple(self.consts)
    self.frozen = True

    for block in self.blocks:
      block.set_addr(self.instr_count)
      self.instr_count += len(block)

    for block in self.blocks:
      block.finalize()

    self.consts = [Box.to_rain(val) for val in self.consts]

  def add_const(self, val):
    if self.frozen:
      raise Exception('{!s} already finalized'.format(self))

    if val in self.consts:
      return self.consts.index(val)

    self.consts.append(val)
    return len(self.consts) - 1

  def add_instr(self, *instrs):
    if self.frozen:
      raise Exception('{!s} already finalized'.format(self))

    self.block.add_instr(*instrs)

  def push_const(self, idx):
    self.add_instr(I.PushConst(idx))

  def push_scope(self):
    self.add_instr(I.PushScope())

  def push_table(self):
    self.add_instr(I.PushTable())

  def pop(self):
    self.add_instr(I.Pop())

  def dup(self, x=0):
    self.add_instr(I.Dup(x))

  def print(self):
    self.add_instr(I.Print())

  def set(self):
    self.add_instr(I.Set())

  def get(self):
    self.add_instr(I.Get())

  def jump(self, offset):
    self.add_instr(I.Jump(offset))

  def jump_if(self, offset):
    self.add_instr(I.JumpIf(offset))

  def jump_ne(self, offset):
    self.add_instr(I.JumpNe(offset))

  def call_to(self, instr):
    self.add_instr(I.CallTo(instr))

  def call(self, argc):
    self.add_instr(I.Call(argc))

  def set_meta(self):
    self.add_instr(I.SetMeta())

  def get_meta(self):
    self.add_instr(I.GetMeta())

  def load(self):
    self.add_instr(I.Load())

  def ret(self):
    self.add_instr(I.Return())

  def save(self):
    self.add_instr(I.Save())

  def fit(self, argc):
    self.add_instr(I.Fit(argc))

  def imp(self):
    self.add_instr(I.Import())

  def add(self):
    self.add_instr(I.BinOp(I.BinOp.ADD))

  def sub(self):
    self.add_instr(I.BinOp(I.BinOp.SUB))

  def mul(self):
    self.add_instr(I.BinOp(I.BinOp.MUL))

  def div(self):
    self.add_instr(I.BinOp(I.BinOp.DIV))

  def lt(self):
    self.add_instr(I.CmpOp(I.CmpOp.LT))

  def le(self):
    self.add_instr(I.CmpOp(I.CmpOp.LE))

  def gt(self):
    self.add_instr(I.CmpOp(I.CmpOp.GT))

  def ge(self):
    self.add_instr(I.CmpOp(I.CmpOp.GE))

  def eq(self):
    self.add_instr(I.CmpOp(I.CmpOp.EQ))

  def ne(self):
    self.add_instr(I.CmpOp(I.CmpOp.NE))

  def nop(self):
    self.add_instr(I.NOP())

  def catch_push(self):
    self.add_instr(I.CatchPush())

  def catch_pop(self):
    self.add_instr(I.CatchPop())

  def write(self):
    self.finalize()

    with open('{0.qname}.rnc'.format(self), 'wb') as fp:
      fp.write(b'RAIN')
      fp.write(struct.pack('<I', len(self.consts)))
      fp.write(struct.pack('<I', self.instr_count))
      fp.write(struct.pack('<I', len(Box._strings_)))

      for string in Box._strings_:
        fp.write(struct.pack('<I', len(string)))
        fp.write(string.encode('utf-8'))

      for const in self.consts:
        fp.write(const)

      for block in self.blocks:
        block.write(fp)

  def add_block(self):
    block = Block()
    self.blocks.append(block)
    return block

  def ins_block(self):
    block = Block()
    pos = self.blocks.index(self.block) + 1
    self.blocks.insert(pos, block)
    return block

  @contextmanager
  def goto(self, block):
    temp = self.block
    self.block = block
    yield
    self.block = temp


  def unpack(self, ls):
    '''Unpack the TOS into the list of names `ls`

    Pops the TOS after completion'''
    for i, key in enumerate(ls):
      i_const = self.add_const(i)
      self.push_const(i_const)
      self.dup(1)
      self.get()

      if isinstance(key, list):
        unpack(key)
      else:
        key_const = self.add_const(key.value)
        self.push_const(key_const)
        self.push_scope()
        self.set()

    self.pop()
