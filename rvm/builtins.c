#include "rain.h"

#define __USE_GNU
#include <dlfcn.h>

void R_builtin_load(R_vm *vm) {
  R_box name = vm_pop(vm);
  R_box lib = vm_pop(vm);
  R_box *ret = &vm->frame->ret;

  if(R_TYPE_IS(&name, STR) && R_TYPE_IS(&lib, STR)) {
    void *handle = dlopen(lib.str, RTLD_LAZY | RTLD_GLOBAL);
    void *func = dlsym(handle, name.str);
    if(func != NULL) {
      R_set_cfunc(ret, func);
      return;
    }
  }

  R_set_null(ret);
}

void R_builtin_print(R_vm *vm) {
  uint32_t args = vm->frame->argc;

  // varargs!
  while(args > 0) {
    R_box pop = vm_pop(vm);
    R_box_print(&pop);
    args -= 1;
  }
}

void R_builtin_scope(R_vm *vm) {
  // push frame -2 scope because we don't want to push this function call's
  // scope, we want its outer scope
  vm_save(vm, &vm->frames[vm->frame_ptr - 2].scope);
}

void R_builtin_meta(R_vm *vm) {
  R_box pop = vm_pop(vm);
  R_box *ret = &vm->frame->ret;

  if(R_has_meta(&pop)) {
    *ret = *(pop.meta);
  }
  else {
    R_set_null(ret);
  }
}

void R_builtin_import(R_vm *vm) {
  R_box pop = vm_pop(vm);

  if(R_TYPE_IS(&pop, STR)) {
    uint32_t module_start = vm->num_instrs;
    vm_import(vm, pop.str);

    // after importing, we need to manipulate the top two frames
    // the runtime will implicitly return after this function, which means
    // we need to trick it into returning to our newly loaded module code.
    // then the loaded module code should return back to where this import()
    // call should return.
    R_frame top = *vm->frame;
    *vm->frame = vm->frames[vm->frame_ptr - 2];
    vm->frames[vm->frame_ptr - 2] = top;
    vm->frame->return_to = module_start - 1;
  }
}

void R_builtin_panic(R_vm *vm) {
  R_box pop = vm_pop(vm);

  vm_recover(vm);

  // after recovering, the VM state is where it was when the catch state was
  // pushed, which means this panic() call's stack frame is gone. because the
  // runtime implicitly returns after this function, we need that stack frame
  // back, and we need to trick it to return to where we want to recover to and
  // what we want to return.
  vm_call(vm, 0, &vm->frame->scope, 0);
  vm_save(vm, &pop);
}
