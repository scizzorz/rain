#ifndef R_BUILTINS_H
#define R_BUILTINS_H

#include "vm.h"

void R_builtin_load(R_vm *vm);
void R_builtin_print(R_vm *vm);
void R_builtin_scope(R_vm *vm);
void R_builtin_meta(R_vm *vm);
void R_builtin_import(R_vm *vm);

#endif
