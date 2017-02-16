from llvmlite import ir
import ctypes as ct
import struct

# indices into a box
TYPE = 0
SIZE = 1
DATA = 2
ENV = 3

# sizes of things
HASH_SIZE = 32

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
box.set_body(i8, i32, i64, arg)
column.set_body(box, box, ptr(column))

# constant aliases
null = box(None)
bin = func(void, [arg, arg, arg])


def _int(val):
  return box([ityp.int, i32(0), cast.int(val), arg(None)])


def _float(val):
  val = cast.float(val).bitcast(cast.int)
  return box([ityp.float, i32(0), val, arg(None)])


def _bool(val):
  return box([ityp.bool, i32(0), cast.bool(int(val)), arg(None)])


def ptrtoint(ptr):
  # need to bullshit around to get this to work - see llvmlite#229
  raw_ir = 'ptrtoint ({0} {1} to {2})'.format(ptr.type, ptr.get_reference(), cast.int)
  return ir.FormattedConstant(cast.int, raw_ir)

def insertvalue(container, value, idx):
  # same as ptrtoint
  raw_ir = 'insertvalue ({0} {1}, {2} {3}, {4})'.format(container.type, container.get_reference(), value.type, value.get_reference(), idx)
  return ir.FormattedConstant(container.type, raw_ir)


def _str(ptr, size):
  return box([ityp.str, i32(size), ptrtoint(ptr), arg(None)])


def _table(ptr):
  return box([ityp.table, i32(0), ptrtoint(ptr), arg(None)])


def _func(ptr=None, args=0):
  if ptr:
    return box([ityp.func, i32(args), ptrtoint(ptr), arg(None)])

  return box([ityp.func, i32(args), i64(0), arg(None)])


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

  def __str__(self):
    return 'cbox({}, {}, {}, {})'.format(self.type, self.size, self.data, self.env)

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
      return cls.new(typi.null, 0, 0, cls.null)
    elif val is False:
      return cls.new(typi.bool, 0, 0, cls.null)
    elif val is True:
      return cls.new(typi.bool, 0, 1, cls.null)
    elif isinstance(val, int):
      return cls.new(typi.int, 0, val, cls.null)
    elif isinstance(val, float):
      raw = struct.pack('d', val)
      intrep = struct.unpack('Q', raw)[0]
      return cls.new(typi.float, 0, intrep, cls.null)
    elif isinstance(val, str):
      str_p = ct.create_string_buffer(val.encode('utf-8'))
      cls._saves_.append(str_p)
      return cls.new(typi.str, len(val), ct.cast(str_p, ct.c_void_p).value, cls.null)

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
cbox._fields_ = [('type', ct.c_uint8),
                 ('size', ct.c_uint32),
                 ('data', ct.c_uint64),
                 ('env', carg)]
cbox.null = carg()
