#include "rain.h"
#define __USE_GNU
#include <dlfcn.h>
#include <string.h>

void (*R_INSTR_TABLE[NUM_INSTRS])(R_vm *, R_op *) = {
  R_PUSH_CONST,
  R_PRINT,
  R_UN_OP,
  R_BIN_OP,
  R_CMP,
  R_JUMP,
  R_JUMPIF,
  R_DUP,
  R_POP,
  R_SET,
  R_GET,
  R_PUSH_TABLE,
  R_PUSH_SCOPE,
  R_NOP,
  R_CALLTO,
  R_RETURN,
  R_IMPORT,
  R_CALL,
  R_SET_META,
  R_GET_META,
  R_LOAD,
  R_SAVE,
  R_FIT,
  R_JUMPNOT,
  R_CATCH_PUSH,
  R_CATCH_POP,
};


const char *R_INSTR_NAMES[NUM_INSTRS] = {
  "PUSH_CONST",
  "PRINT",
  "UN_OP",
  "BIN_OP",
  "CMP",
  "JUMP",
  "JUMPIF",
  "DUP",
  "POP",
  "SET",
  "GET",
  "PUSH_TABLE",
  "PUSH_SCOPE",
  "NOP",
  "CALLTO",
  "RETURN",
  "IMPORT",
  "CALL",
  "SET_META",
  "GET_META",
  "LOAD",
  "SAVE",
  "FIT",
  "JUMPNOT",
  "CATCH_PUSH",
  "CATCH_POP",
};

void R_PRINT(R_vm *vm, R_op *instr) {
  fprintf(stderr, "Deprecated use of PRINT instruction\n");
  R_box val = vm_pop(vm);
  R_box_print(&val);
}


void R_PUSH_CONST(R_vm *vm, R_op *instr) {
  vm_push(vm, &vm->consts[R_UI(instr)]);
}

void R_PUSH_SCOPE(R_vm *vm, R_op *instr) {
  vm_push(vm, &vm->frames[vm->frame_ptr - 1].scope);
}

void R_UN_OP(R_vm *vm, R_op *instr) {
  R_box *val = &vm->stack[vm->stack_ptr - 1];

  if(R_UI(instr) == UN_NEG) {
    switch(val->type) {
      case R_TYPE_INT:
        val->i64 = -val->i64;
        return;
      case R_TYPE_FLOAT:
        val->f64 = -val->f64;
        return;
    }
  }

  if(R_UI(instr) == UN_NOT) {
    R_set_bool(val, val->type == R_TYPE_NULL || (val->type == R_TYPE_BOOL && val->i64 == 0));
    return;
  }

  if(R_UI(instr) == UN_STR) {
    R_box_to_str(val, val);
    return;
  }

  R_set_null(val);
}

void R_BIN_OP(R_vm *vm, R_op *instr) {
  R_box rhs = vm_pop(vm);
  R_box lhs = vm_top(vm);
  R_box *top = &vm->stack[vm->stack_ptr - 1];
  bool do_float = false;
  double lhs_f, rhs_f;

  if(R_UI(instr) == BIN_CAT) {
    R_box_to_str(&lhs, &lhs);
    R_box_to_str(&rhs, &rhs);
    char *cat = GC_malloc(lhs.size + rhs.size + 1);

    strcat(cat, lhs.str);
    strcat(cat + lhs.size, rhs.str);
    R_set_str(top, cat);

    return;
  }

  if(R_TYPE_IS(&lhs, INT) && R_TYPE_IS(&rhs, INT)) {
    switch(R_UI(instr)) {
      case BIN_ADD: R_set_int(top, lhs.i64 + rhs.i64); break;
      case BIN_SUB: R_set_int(top, lhs.i64 - rhs.i64); break;
      case BIN_MUL: R_set_int(top, lhs.i64 * rhs.i64); break;
      case BIN_DIV: R_set_int(top, lhs.i64 / rhs.i64); break;
    }
    return;
  }
  else if(R_TYPE_IS(&lhs, FLOAT) && R_TYPE_IS(&rhs, INT)) {
    lhs_f = lhs.f64;
    rhs_f = (double)rhs.i64;
    do_float = true;
  }
  else if(R_TYPE_IS(&lhs, INT) && R_TYPE_IS(&rhs, FLOAT)) {
    lhs_f = (double)lhs.i64;
    rhs_f = rhs.f64;
    do_float = true;
  }
  else if(R_TYPE_IS(&lhs, FLOAT) && R_TYPE_IS(&rhs, FLOAT)) {
    lhs_f = lhs.f64;
    rhs_f = rhs.f64;
    do_float = true;
  }

  if(do_float) {
    switch(R_UI(instr)) {
      case BIN_ADD: R_set_float(top, lhs_f + rhs_f); break;
      case BIN_SUB: R_set_float(top, lhs_f - rhs_f); break;
      case BIN_MUL: R_set_float(top, lhs_f * rhs_f); break;
      case BIN_DIV: R_set_float(top, lhs_f / rhs_f); break;
    }
    return;
  }

  R_set_null(top);
}

void R_CMP(R_vm *vm, R_op *instr) {
  R_box rhs = vm_pop(vm);
  R_box lhs = vm_top(vm);
  R_box *top = &vm->stack[vm->stack_ptr - 1];

  if(lhs.type != rhs.type) {
    R_set_bool(top, R_UI(instr) == CMP_NE);
    return;
  }

  if(R_TYPE_IS(&lhs, INT) && R_TYPE_IS(&rhs, INT)) {
    switch(R_UI(instr)) {
      case CMP_LT: R_set_bool(top, lhs.i64 < rhs.i64); break;
      case CMP_LE: R_set_bool(top, lhs.i64 <= rhs.i64); break;
      case CMP_GT: R_set_bool(top, lhs.i64 > rhs.i64); break;
      case CMP_GE: R_set_bool(top, lhs.i64 >= rhs.i64); break;
      case CMP_EQ: R_set_bool(top, lhs.i64 == rhs.i64); break;
      case CMP_NE: R_set_bool(top, lhs.i64 != rhs.i64); break;
    }
    return;
  }

  // TODO: add int/float and float/int comparisons?
  else if(R_TYPE_IS(&lhs, FLOAT) && R_TYPE_IS(&rhs, FLOAT)) {
    switch(R_UI(instr)) {
      case CMP_LT: R_set_bool(top, lhs.f64 < rhs.f64); break;
      case CMP_LE: R_set_bool(top, lhs.f64 <= rhs.f64); break;
      case CMP_GT: R_set_bool(top, lhs.f64 > rhs.f64); break;
      case CMP_GE: R_set_bool(top, lhs.f64 >= rhs.f64); break;
      case CMP_EQ: R_set_bool(top, lhs.f64 == rhs.f64); break;
      case CMP_NE: R_set_bool(top, lhs.f64 != rhs.f64); break;
    }
    return;
  }

  else if(R_TYPE_IS(&lhs, BOOL) && R_TYPE_IS(&rhs, BOOL)) {
    switch(R_UI(instr)) {
      case CMP_LT: R_set_bool(top, lhs.u64 < rhs.u64); break;
      case CMP_LE: R_set_bool(top, lhs.u64 <= rhs.u64); break;
      case CMP_GT: R_set_bool(top, lhs.u64 > rhs.u64); break;
      case CMP_GE: R_set_bool(top, lhs.u64 >= rhs.u64); break;
      case CMP_EQ: R_set_bool(top, lhs.u64 == rhs.u64); break;
      case CMP_NE: R_set_bool(top, lhs.u64 != rhs.u64); break;
    }
    return;
  }

  else if(R_TYPE_IS(&lhs, NULL) && R_TYPE_IS(&rhs, NULL)) {
    switch(R_UI(instr)) {
      case CMP_LT: R_set_bool(top, false); break;
      case CMP_LE: R_set_bool(top, true); break;
      case CMP_GT: R_set_bool(top, false); break;
      case CMP_GE: R_set_bool(top, true); break;
      case CMP_EQ: R_set_bool(top, true); break;
      case CMP_NE: R_set_bool(top, true); break;
    }
    return;
  }

  R_set_null(top);
}


void R_JUMP(R_vm *vm, R_op *instr) {
  vm->instr_ptr += R_SI(instr);
}


void R_JUMPIF(R_vm *vm, R_op *instr) {
  R_box top = vm_pop(vm);

  if(top.type != R_TYPE_NULL && !(top.type == R_TYPE_BOOL && top.i64 == 0)) {
    vm->instr_ptr += R_SI(instr);
    // TODO: what if IP goes out of bounds?
  }
}


void R_DUP(R_vm *vm, R_op *instr) {
  R_box *top = &vm->stack[vm->stack_ptr - 1 - R_UI(instr)];
  vm_push(vm, top);
}


void R_POP(R_vm *vm, R_op *instr) {
  vm_pop(vm);
}


void R_SET(R_vm *vm, R_op *instr) {
  R_box table = vm_pop(vm);
  R_box key = vm_pop(vm);
  R_box val = vm_pop(vm);
  R_table_set(&table, &key, &val);
}


void R_GET(R_vm *vm, R_op *instr) {
  R_box table = vm_pop(vm);
  R_box *cur = &table;
  R_box key = vm_top(vm);
  R_box *top = &vm->stack[vm->stack_ptr - 1];
  R_box *res;
  while(cur != NULL) {
    res = R_table_get(cur, &key);

    if(res != NULL) {
      *top = *res;
      return;
    }

    if(R_has_meta(cur)) {
      cur = cur->meta;
      continue;
    }

    break;
  }

  R_set_null(top);
}

void R_PUSH_TABLE(R_vm *vm, R_op *instr) {
  R_set_table(&vm->stack[vm->stack_ptr]);
  vm->stack_ptr += 1;
}

void R_NOP(R_vm *vm, R_op *instr) {
}

void R_CALLTO(R_vm *vm, R_op *instr) {
  vm_call(vm, R_UI(instr) - 1, NULL, 0);
}

void R_RETURN(R_vm *vm, R_op *instr) {
  vm_ret(vm);
}

void R_IMPORT(R_vm *vm, R_op *instr) {
  fprintf(stderr, "Deprecated use of IMPORT instruction\n");
  R_box pop = vm_pop(vm);
  if(R_TYPE_IS(&pop, STR)) {
    vm_import(vm, pop.str);
    vm->instr_ptr -= 1;
  }
}

void R_CALL(R_vm *vm, R_op *instr) {
  R_box pop = vm_pop(vm);
  R_box scope;

  if(R_TYPE_IS(&pop, FUNC)) {
    if(R_has_meta(&pop)) {
      R_table_clone(pop.meta, &scope);
    }
    else {
      R_set_table(&scope);
    }

    vm_call(vm, pop.u64 - 1, &scope, R_UI(instr));
  }

  else if(R_TYPE_IS(&pop, CFUNC)) {
    if(R_has_meta(&pop)) {
      R_table_clone(pop.meta, &scope);
    }
    else {
      R_set_table(&scope);
    }

    vm_call(vm, vm->instr_ptr, &scope, R_UI(instr));

    void (*fn)(R_vm *) = (void (*)(R_vm *))pop.ptr;
    fn(vm);

    vm_ret(vm);
  }
}

void R_SET_META(R_vm *vm, R_op *instr) {
  R_box pop = vm_pop(vm);
  R_box *top = &vm->stack[vm->stack_ptr - 1];
  top->meta = GC_malloc(sizeof(R_box));
  *(top->meta) = pop;
}

void R_GET_META(R_vm *vm, R_op *instr) {
  R_box pop = vm_pop(vm);
  vm_push(vm, pop.meta);
}

void R_LOAD(R_vm *vm, R_op *instr) {
  fprintf(stderr, "Deprecated use of LOAD instruction\n");
  R_box name = vm_pop(vm);
  R_box lib = vm_top(vm);
  R_box *top = &vm->stack[vm->stack_ptr - 1];

  if(R_TYPE_IS(&name, STR) && R_TYPE_IS(&lib, STR)) {
    void *handle = dlopen(lib.str, RTLD_LAZY | RTLD_GLOBAL);
    void *func = dlsym(handle, name.str);
    R_set_cfunc(top, func);
    return;
  }

  R_set_null(top);
}

void R_SAVE(R_vm *vm, R_op *instr) {
  R_box pop = vm_pop(vm);
  vm->frame->ret = pop;
}

void R_FIT(R_vm *vm, R_op *instr) {
  vm_fit(vm, R_UI(instr));
}


void R_JUMPNOT(R_vm *vm, R_op *instr) {
  R_box top = vm_pop(vm);

  if(top.type == R_TYPE_NULL || (top.type == R_TYPE_BOOL && top.i64 == 0)) {
    vm->instr_ptr += R_SI(instr);
    // TODO: what if IP goes out of bounds?
  }
}

void R_CATCH_PUSH(R_vm *vm, R_op *instr) {
  vm_catch_push(vm);
}

void R_CATCH_POP(R_vm *vm, R_op *instr) {
  vm_catch_pop(vm);
}
