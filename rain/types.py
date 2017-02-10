from llvmlite import ir
import ctypes as ct
import struct

# indices into a box
TYPE = 0
DATA = 1
SIZE = 2

# sizes of things
BOX_SIZE = 24
HASH_SIZE = 32
TRAMP_SIZE = 72

# all sorts of type aliases
i8 = ir.IntType(8)
i32 = ir.IntType(32)
i64 = ir.IntType(64)
f32 = ir.FloatType()
f64 = ir.DoubleType()
void = ir.VoidType()
func = ir.FunctionType
ptr = ir.PointerType
arr = ir.ArrayType
box = ir.context.global_context.get_identified_type('box')
column = ir.context.global_context.get_identified_type('column')
arg = ptr(box)
lp = ir.LiteralStructType([ptr(i8), i32])


def vfunc(*args, var_arg=False):
  return func(void, args, var_arg=var_arg)


# set struct bodies
box.set_body(i8, i64, i32)
column.set_body(box, box, ptr(column))

# constant aliases
null = box(None)
bin = func(void, [arg, arg, arg])


def _int(val):
  return box([ityp.int, cast.int(val), i32(0)])


def _float(val):
  val = cast.float(val).bitcast(cast.int)
  return box([ityp.float, val, i32(0)])


def _bool(val):
  return box([ityp.bool, cast.bool(int(val)), i32(0)])


def ptrtoint(ptr):
  # need to bullshit around to get this to work - see llvmlite#229
  raw_ir = 'ptrtoint ({0} {1} to {2})'.format(ptr.type, ptr.get_reference(), cast.int)
  return ir.FormattedConstant(cast.int, raw_ir)


def _str(ptr, size):
  return box([ityp.str, ptrtoint(ptr), i32(size)])


def _table(ptr):
  return box([ityp.table, ptrtoint(ptr), i32(0)])


def _func(ptr=None, args=0):
  if ptr:
    return box([ityp.func, ptrtoint(ptr), i32(args)])

  return box([ityp.func, i64(0), i32(args)])


class cast:
  null = i64
  int = i64
  float = f64
  bool = i64
  str = ptr(i8)
  table = ptr(ptr(column))
  func = ptr(i8)


class typi:
  null = 0
  int = 1
  float = 2
  bool = 3
  str = 4
  table = 5
  func = 6
  cdata = 7


class ityp:
  null = i8(typi.null)
  int = i8(typi.int)
  float = i8(typi.float)
  bool = i8(typi.bool)
  str = i8(typi.str)
  table = i8(typi.table)
  func = i8(typi.func)
  cdata = i8(typi.cdata)


class cbox(ct.Structure):
  _saves_ = []
  _fields_ = [('type', ct.c_uint8),
              ('data', ct.c_uint64),
              ('size', ct.c_uint32)]

  def __str__(self):
    return 'cbox({}, {}, {})'.format(self.type, self.data, self.size)

  def __repr__(self):
    return '<{!s}>'.format(self)

  @classmethod
  def new(cls, *args, **kwargs):
    obj = cls(*args, **kwargs)
    cls._saves_.append(obj)
    return obj

  @classmethod
  def from_str(cls, string):
    str_p = ct.create_string_buffer(string.encode('utf-8'))
    cls._saves_.append(str_p)
    return cls.new(typi.str, ct.cast(str_p, ct.c_void_p).value, len(string))

  def as_str(self):
    return ct.cast(self.data, ct.c_char_p).value.decode('utf-8')

  @classmethod
  def to_rain(cls, val):
    if val is None:
      return cls.new(typi.null, 0, 0)
    elif val is False:
      return cls.new(typi.bool, 0, 0)
    elif val is True:
      return cls.new(typi.bool, 1, 0)
    elif isinstance(val, int):
      return cls.new(typi.int, val, 0)
    elif isinstance(val, float):
      raw = struct.pack('d', val)
      intrep = struct.unpack('Q', raw)[0]
      return cls.new(typi.float, intrep, 0)
    elif isinstance(val, str):
      str_p = ct.create_string_buffer(val.encode('utf-8'))
      cls._saves_.append(str_p)
      return cls.new(typi.str, ct.cast(str_p, ct.c_void_p).value, len(val))

    raise Exception("Can't convert value {!r} to Rain".format(val))

  def to_py(self):
    if self.type == typi.null:
      return None
    elif self.type == typi.bool:
      return bool(self.data)
    elif self.type == typi.int:
      return self.data
    elif self.type == typi.float:
      raw = struct.pack('Q', self.data)
      floatrep = struct.unpack('d', raw)[0]
      return floatrep
    elif self.type == typi.str:
      return ct.cast(self.data, ct.c_char_p).value.decode('utf-8')

    raise Exception("Can't convert value {!r} to Python".format(self))


carg = ct.POINTER(cbox)
