from llvmlite import ir

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

  return box([ityp.func, i64(0), i32(0)])

class cast:
  null = i64
  int = i64
  float = f64
  bool = i64
  str = ptr(i8)
  table = ptr(ptr(column))
  func = ptr(i8)

class ityp:
  null = i8(0)
  int = i8(1)
  float = i8(2)
  bool = i8(3)
  str = i8(4)
  table = i8(5)
  func = i8(6)
  cdata = i8(7)
