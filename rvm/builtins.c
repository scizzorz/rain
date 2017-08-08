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
  printf("importing: ");
  R_box_print(&pop);
  if(R_TYPE_IS(&pop, STR)) {
    uint32_t module_start = vm->num_instrs;
    vm_import(vm, pop.str);
    R_frame top = *vm->frame;
    *vm->frame = vm->frames[vm->frame_ptr - 2];
    vm->frames[vm->frame_ptr - 2] = top;
    vm->frame->return_to = module_start - 1;
  }
}
