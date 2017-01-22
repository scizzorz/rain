from llvmlite import ir
from llvmlite import binding

mod = ir.Module(name='test')
mod.triple = binding.get_default_triple()

struct_unwind_exception = ir.context.global_context.get_identified_type('struct._Unwind_Exception')
struct_unwind_exception = ir.context.global_context.get_identified_type('struct._Unwind_Context')
box = ir.context.global_context.get_identified_type('box')
box.set_body(ir.IntType(8), ir.IntType(64), ir.IntType(32))

landingpad_type = ir.LiteralStructType([ir.IntType(8).as_pointer(), ir.IntType(32)])

rain_personality = ir.Function(mod, ir.FunctionType(ir.IntType(32), [], var_arg=True), name='rain_personality_v0')
rain_print = ir.Function(mod, ir.FunctionType(ir.VoidType(), [box.as_pointer()]), name='rain_print')
rain_throw = ir.Function(mod, ir.FunctionType(ir.VoidType(), [box.as_pointer()]), name='rain_throw')
rain_catch = ir.Function(mod, ir.FunctionType(ir.VoidType(), [box.as_pointer()]), name='rain_catch')

main = ir.Function(mod, ir.FunctionType(ir.IntType(32), []), name='main')
main.attributes.personality = rain_personality

# entry
block = main.append_basic_block(name='entry')
entry_builder = ir.IRBuilder(block)

# catch
block = main.append_basic_block(name='catch')
lp_builder = ir.IRBuilder(block)

# return
block = main.append_basic_block(name='ret')
ret_builder = ir.IRBuilder(block)

# define entry
arg_ptr = entry_builder.alloca(box)
entry_builder.store(box([1, 10, 0]), arg_ptr)
entry_builder.invoke(rain_throw, [arg_ptr], ret_builder.block, lp_builder.block)

# define landingpad
lp = lp_builder.landingpad(landingpad_type, name='test')
lp.add_clause(ir.CatchClause(ir.IntType(8).as_pointer()(None)))
exc_ptr = lp_builder.alloca(box)
lp_builder.store(box(None), exc_ptr)
lp_builder.call(rain_catch, [exc_ptr])
lp_builder.call(rain_print, [exc_ptr])
lp_builder.branch(ret_builder.block)

# define return
ret_builder.ret(ir.IntType(32)(0))

# output
print(mod)
with open('test.ll', 'w') as tmp:
  tmp.write(str(mod))
