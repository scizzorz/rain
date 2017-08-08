#ifndef R_VM_H
#define R_VM_H

#include "core.h"
#include <stdbool.h>

typedef struct R_header {
  uint32_t num_consts;
  uint32_t num_instrs;
  uint32_t num_strings;
} R_header;

typedef struct R_frame {
  uint32_t return_to;
  uint32_t base_ptr;
  uint32_t argc;
  R_box scope;
  R_box ret;
} R_frame;

typedef struct R_vm {
  uint32_t instr_ptr;
  uint32_t num_consts;
  uint32_t num_instrs;
  uint32_t num_strings;

  uint32_t stack_ptr;
  uint32_t stack_size;

  uint32_t scope_ptr;
  uint32_t scope_size;

  uint32_t frame_ptr;
  uint32_t frame_size;

  char **strings;
  R_box *consts;
  R_op *instrs;
  R_box *stack;
  R_frame *frames;
  R_frame *frame;
} R_vm;

R_vm *vm_new();
bool vm_import(R_vm *this, const char *fname);
bool vm_load(R_vm *this, FILE *fp);
bool vm_exec(R_vm *this, R_op *instr);
bool vm_step(R_vm *this);
bool vm_run(R_vm *this);
void vm_dump(R_vm *this);
R_box vm_pop(R_vm *this);
R_box vm_top(R_vm *this);
R_box *vm_push(R_vm *this, R_box *val);
R_box *vm_alloc(R_vm *this);
void vm_set(R_vm *this, R_box *val);
void vm_call(R_vm *this, uint32_t to, R_box *scope, uint32_t argc);
void vm_ret(R_vm *this);
void vm_save(R_vm *this, R_box *val);
void vm_fit(R_vm *this, uint32_t want);

#endif
