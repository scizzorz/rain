#include "rain.h"
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

void R_box_print(R_box *val) {
  switch(val->type) {
    case R_TYPE_NULL:
      printf("null\n");
      break;
    case R_TYPE_INT:
      printf("%ld\n", val->i64);
      break;
    case R_TYPE_FLOAT:
      printf("%f\n", val->f64);
      break;
    case R_TYPE_BOOL:
      printf(val->i64 != 0 ? "true\n" : "false\n");
      break;
    case R_TYPE_STR:
      printf("%s\n", val->str);
      break;
    case R_TYPE_TABLE:
      printf("table 0x%08lx\n", (unsigned long)val->ptr);
      break;
    case R_TYPE_FUNC:
      printf("func 0x%04lx\n", val->u64);
      break;
    case R_TYPE_CFUNC:
      printf("cfunc 0x%08lx\n", (unsigned long)val->ptr);
      break;
    case R_TYPE_CDATA:
      printf("cdata 0x%08lx\n", (unsigned long)val->ptr);
      break;
    default:
      printf("unknown\n");
  }
}

bool R_has_meta(R_box *val) {
  return (val->meta != NULL) && (R_TYPE_ISNT(val->meta, NULL));
}

void R_set_box(R_box *ret, R_box *from) {
  ret->type = from->type;
  ret->u64 = from->u64;
  ret->size = from->size;
  ret->meta = from->meta;
}

void R_set_null(R_box *ret) {
  ret->type = R_TYPE_NULL;
  ret->u64 = 0;
  ret->size = 0;
  ret->meta = NULL;
}

void R_set_int(R_box *ret, signed long si) {
  ret->type = R_TYPE_INT;
  ret->i64 = si;
  ret->size = 0;
  ret->meta = NULL;
}

void R_set_float(R_box *ret, double f) {
  ret->type = R_TYPE_FLOAT;
  ret->f64 = f;
  ret->size = 0;
  ret->meta = NULL;
}

void R_set_bool(R_box *ret, bool v) {
  ret->type = R_TYPE_BOOL;
  ret->u64 = v;
  ret->size = 0;
  ret->meta = NULL;
}

void R_set_str(R_box *ret, char *s) {
  ret->type = R_TYPE_STR;
  ret->str = s;
  ret->size = strlen(s);
  ret->meta = NULL;
}

void R_set_strcpy(R_box *ret, const char *s) {
  int size = strlen(s);

  ret->type = R_TYPE_STR;
  ret->str = GC_malloc(size + 1);
  ret->size = size;

  memcpy(ret->str, s, size);
  ret->str[size] = 0;
  ret->meta = NULL;
}

void R_set_table_sized(R_box *ret, uint32_t size) {
  R_table *table = GC_malloc(sizeof(R_table));
  table->cur = 0;
  table->max = size;
  table->items = GC_malloc(sizeof(R_item *) * size);

  ret->type = R_TYPE_TABLE;
  ret->table = table;
  ret->size = 0;
  ret->meta = NULL;
}

void R_set_table(R_box *ret) {
  R_set_table_sized(ret, R_INIT_TABLE_SIZE);
}

void R_set_cfunc(R_box *ret, void *p) {
  ret->type = R_TYPE_CFUNC;
  ret->ptr = p;
  ret->size = 0;
  ret->meta = NULL;
}

void R_set_cdata(R_box *ret, void *p) {
  ret->type = R_TYPE_CDATA;
  ret->ptr = p;
  ret->size = 0;
  ret->meta = NULL;
}

void R_set_meta(R_box *val, R_box *meta) {
  val->meta = meta;
}

void R_op_print(R_op *instr) {
  switch(R_OP(instr)) {
    case PUSH_CONST:
    case BIN_OP:
    case UN_OP:
    case CMP:
    case CALL:
    case FIT:
      printf("%s (%d)\n", R_INSTR_NAMES[R_OP(instr)], R_UI(instr));
      break;
    case JUMP:
    case JUMPIF:
      printf("%s (%d)\n", R_INSTR_NAMES[R_OP(instr)], R_SI(instr));
      break;
    case CALLTO:
      printf("%s (%02x)\n", R_INSTR_NAMES[R_OP(instr)], R_UI(instr));
      break;
    default:
      printf("%s\n", R_INSTR_NAMES[R_OP(instr)]);
  }
}
