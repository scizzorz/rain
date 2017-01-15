from llvmlite import ir

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
box.set_body(i8, i64, i32)

column = ir.context.global_context.get_identified_type('column')
column.set_body(box, box, ptr(column))

entry = ir.context.global_context.get_identified_type('entry')
entry.set_body(ptr(box), ptr(box), ptr(entry))

bin = func(void, [ptr(box), ptr(box), ptr(box)])

def vfunc(*args, var_arg=False):
  return func(void, args, var_arg=var_arg)

class cast:
  null = i64
  int = i64
  float = f64
  bool = i64
  str = ptr(i8)
  table = ptr(ptr(entry))
  func = ptr(i8)

class ityp:
  null = i8(0)
  int = i8(1)
  float = i8(2)
  bool = i8(3)
  str = i8(4)
  table = i8(5)
  func = i8(6)
  data = i8(7)
