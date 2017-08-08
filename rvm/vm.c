#include "rain.h"

#include <limits.h>

R_vm *vm_new() {
  GC_init();

  R_vm *this = GC_malloc(sizeof(R_vm));

  this->num_consts = 0;
  this->num_instrs = 0;
  this->num_strings = 0;

  this->instr_ptr = UINT32_MAX - 1;
  this->stack_ptr = 0;
  this->scope_ptr = 0;
  this->frame_ptr = 0;

  this->stack_size = 10;
  this->scope_size = 10;
  this->frame_size = 10;

  this->consts = GC_malloc(sizeof(R_box));
  this->instrs = GC_malloc(sizeof(R_op));
  this->strings = GC_malloc(sizeof(char *));

  this->stack = GC_malloc(sizeof(R_box) * this->stack_size);
  this->frames = GC_malloc(sizeof(R_frame) * this->frame_size);

  return this;
}

bool vm_import(R_vm *this, const char *fname) {
  FILE *fp = fopen(fname, "rb");

  if(fp == NULL) {
    fprintf(stderr, "Unable to open file %s\n", fname);
    return false;
  }

  uint32_t module_start = this->num_instrs;
  if(!vm_load(this, fp)) {
    fprintf(stderr, "Unable to load bytecode\n");
    fclose(fp);
    return false;
  }

  R_box builtins;
  R_box key;
  R_box val;

  R_set_table(&builtins);
  R_set_str(&key, "load");
  R_set_cfunc(&val, R_builtin_load);
  R_table_set(&builtins, &key, &val);

  R_set_str(&key, "print");
  R_set_cfunc(&val, R_builtin_print);
  R_table_set(&builtins, &key, &val);

  R_set_str(&key, "meta");
  R_set_cfunc(&val, R_builtin_meta);
  R_table_set(&builtins, &key, &val);

  R_set_str(&key, "scope");
  R_set_cfunc(&val, R_builtin_scope);
  R_table_set(&builtins, &key, &val);

  R_set_str(&key, "import");
  R_set_cfunc(&val, R_builtin_import);
  R_table_set(&builtins, &key, &val);

  vm_call(this, module_start, &builtins, 0);
  return true;
}

bool vm_load(R_vm *this, FILE *fp) {
  size_t rv;
  R_header header;

  // save previous counts
  uint32_t prev_consts = this->num_consts;
  uint32_t prev_instrs = this->num_instrs;
  uint32_t prev_strings = this->num_strings;

  // read header information
  rv = fread(&header, sizeof(R_header), 1, fp);
  if(rv != 1) {
    fprintf(stderr, "Unable to read header\n");
    return false;
  }

  // increment counts
  this->num_consts += header.num_consts;
  this->num_instrs += header.num_instrs;
  this->num_strings += header.num_strings;

  // resize arrays
  this->consts = GC_realloc(this->consts, sizeof(R_box) * this->num_consts);
  this->instrs = GC_realloc(this->instrs, sizeof(R_op) * this->num_instrs);
  this->strings = GC_realloc(this->strings, sizeof(char *) * this->num_strings);

  // read all strings
  uint32_t len = 0;
  for(uint32_t i=prev_strings; i<this->num_strings; i++) {
    rv = fread(&len, sizeof(int), 1, fp);
    if(rv != 1) {
      fprintf(stderr, "Unable to read string %d length\n", i);
      return false;
    }

    this->strings[i] = GC_malloc_atomic(len + 1);
    rv = fread(this->strings[i], 1, len, fp);
    if(rv != len) {
      fprintf(stderr, "Unable to read string %d\n", i);
      return false;
    }

    this->strings[i][len] = 0;
  }

  // read all constants
  rv = fread(this->consts + prev_consts, sizeof(R_box), header.num_consts, fp);
  if(rv != header.num_consts) {
    fprintf(stderr, "Unable to read constants\n");
    return false;
  }

  // read all instructions
  rv = fread(this->instrs + prev_instrs, sizeof(R_op), header.num_instrs, fp);
  if(rv != header.num_instrs) {
    fprintf(stderr, "Unable to read instructions\n");
    return false;
  }

  // adjust string const pointers
  for(uint32_t i=prev_consts; i<this->num_consts; i++) {
    if(R_TYPE_IS(&this->consts[i], STR)) {
      this->consts[i].str = this->strings[this->consts[i].i64 + prev_strings];
    }
    else if(R_TYPE_IS(&this->consts[i], FUNC)) {
      this->consts[i].u64 += prev_instrs;
    }
  }

  // adjust instruction indices
  for(uint32_t i=prev_instrs; i<this->num_instrs; i++) {
    switch(R_OP(&this->instrs[i])) {
      case PUSH_CONST:
        this->instrs[i].u32 += prev_consts << 8;
        break;
      case CALLTO:
        this->instrs[i].u32 += prev_instrs << 8;
        break;
    }
  }

  return true;
}

bool vm_exec(R_vm *this, R_op *instr) {
  if(R_OP(instr) < NUM_INSTRS) {
    R_INSTR_TABLE[R_OP(instr)](this, instr);
    return true;
  }

  printf("Unknown instruction %02x %06x\n", R_OP(instr), R_UI(instr));
  return false;
}

bool vm_step(R_vm *this) {
  if(this->instr_ptr < this->num_instrs) {
    if(vm_exec(this, this->instrs + this->instr_ptr)) {
      this->instr_ptr += 1;
      return true;
    }
  }

  return false;
}

bool vm_run(R_vm *this) {
  while(this->instr_ptr < this->num_instrs) {
    vm_step(this);
  }

  return true;
}

void vm_dump(R_vm *this) {
  printf("Constants (%d):\n", this->num_consts);
  for(uint32_t i=0; i<this->num_consts; i++) {
    printf("   ");
    R_box_print(this->consts + i);
  }

  printf("Instructions (%d):\n", this->num_instrs);
  for(uint32_t i=0; i<this->num_instrs; i++) {
    printf("%02x", i);
    printf(i == this->instr_ptr ? " > " : "   ");
    R_op_print(this->instrs + i);
  }

  printf("Stack (%d / %d):\n", this->stack_ptr, this->stack_size);
  for(uint32_t i=0; i<this->stack_size; i++) {
    if(i + 1 > this->stack_ptr) {
      printf("     ");
    }
    else if(i + 1 == this->stack_ptr) {
      printf("% 2d > ", i);
    }
    else {
      printf("% 2d   ", i);
    }

    R_box_print(this->stack + i);
  }

  printf("Frames (%d / %d):\n", this->frame_ptr, this->frame_size);
  for(uint32_t i=0; i<this->frame_ptr; i++) {
    printf("%02x    ", this->frames[i].return_to);
    if(this->frames[i].return_to < this->num_instrs) {
      R_op_print(this->instrs + this->frames[i].return_to);
    }
    else {
      printf("???\n");
    }
    printf("   base_ptr = %d, argc = %d\n", this->frames[i].base_ptr, this->frames[i].argc);
  }
}

R_box vm_pop(R_vm *this) {
  this->stack_ptr -= 1;
  return this->stack[this->stack_ptr];
}

R_box vm_top(R_vm *this) {
  return this->stack[this->stack_ptr - 1];
}

void vm_set(R_vm *this, R_box *val) {
  this->stack[this->stack_ptr - 1] = *val;
}

R_box *vm_alloc(R_vm *this) {
  if(this->stack_ptr >= this->stack_size) {
    this->stack_size *= 2;
    this->stack = GC_realloc(this->stack, sizeof(R_box) * this->stack_size);
  }

  R_set_null(&this->stack[this->stack_ptr]);
  this->stack_ptr += 1;

  return &this->stack[this->stack_ptr - 1];
}

R_box *vm_push(R_vm *this, R_box *val) {
  if(this->stack_ptr >= this->stack_size) {
    this->stack_size *= 2;
    this->stack = GC_realloc(this->stack, sizeof(R_box) * this->stack_size);
  }

  this->stack[this->stack_ptr] = *val;
  this->stack_ptr += 1;

  return &this->stack[this->stack_ptr - 1];
}

void vm_call(R_vm *this, uint32_t to, R_box *scope, uint32_t argc) {
  this->frame = &this->frames[this->frame_ptr];
  this->frame->return_to = this->instr_ptr;
  this->frame->argc = argc;
  this->frame->base_ptr = this->stack_ptr - argc;
  R_set_null(&this->frame->ret);

  if(scope == NULL) {
    R_set_table(&this->frame->scope);
  }
  else {
    this->frame->scope = *scope;
  }

  this->frame_ptr += 1;
  this->instr_ptr = to;
}

void vm_ret(R_vm *this) {
  this->instr_ptr = this->frame->return_to;
  this->stack_ptr = this->frame->base_ptr;
  vm_push(this, &this->frame->ret);

  this->frame_ptr -= 1;
  this->frame = &this->frames[this->frame_ptr - 1];
}

void vm_save(R_vm *this, R_box *val) {
  this->frame->ret = *val;
}

void vm_fit(R_vm *this, uint32_t want) {
  uint32_t have = this->frame->argc;
  R_box null;
  R_set_null(&null);

  while(have < want) {
    vm_push(this, &null);
    have += 1;
  }

  while(have > want) {
    vm_pop(this);
    have -= 1;
  }
}
