from llvmlite import ir
from llvmlite import binding

mod = ir.Module(name='test')
mod.triple = binding.get_default_triple()

struct_unwind_exception = ir.context.global_context.get_identified_type('struct._Unwind_Exception')
struct_unwind_exception = ir.context.global_context.get_identified_type('struct._Unwind_Context')

landingpad_type = ir.LiteralStructType([ir.IntType(8).as_pointer(), ir.IntType(32)])

rain_personality = ir.Function(mod, ir.FunctionType(ir.IntType(32), [], var_arg=True), name='rain_personality')
rain_throw = ir.Function(mod, ir.FunctionType(ir.VoidType(), []), name='rain_throw')
rain_catch = ir.Function(mod, ir.FunctionType(ir.VoidType(), [ir.IntType(32)]), name='rain_catch')

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
entry_builder.call(rain_catch, [ir.IntType(32)(0)])
entry_builder.invoke(rain_throw, [], ret_builder.block, lp_builder.block)
#entry_builder.branch(ret_builder.block)

# define landingpad
lp = lp_builder.landingpad(landingpad_type, name='test')
lp.add_clause(ir.CatchClause(ir.IntType(8).as_pointer()(None)))
lp_builder.call(rain_catch, [ir.IntType(32)(1)])
lp_builder.branch(ret_builder.block)

# define return
ret_builder.ret(ir.IntType(32)(0))

# output
print(mod)
with open('test.ll', 'w') as tmp:
  tmp.write(str(mod))
