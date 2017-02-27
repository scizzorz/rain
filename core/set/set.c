#include "../rain.h"
#include <gc.h>
#include <stdlib.h>
#include <string.h>


// box helpers

void rain_set_box(box *ret, box *from) {
  ret->type = from->type;
  ret->data.ui = from->data.ui;
  ret->size = from->size;
  ret->env = from->env;
}

void rain_set_null(box *ret) {
  ret->type = ITYP_NULL;
  ret->data.ui = 0;
  ret->size = 0;
  ret->env = NULL;
}

void rain_set_int(box *ret, signed long si) {
  ret->type = ITYP_INT;
  ret->data.si = si;
  ret->size = 0;
  ret->env = rain_vt_int;
}

void rain_set_float(box *ret, double f) {
  ret->type = ITYP_FLOAT;
  ret->data.f = f;
  ret->size = 0;
  ret->env = rain_vt_float;
}

void rain_set_bool(box *ret, unsigned char v) {
  ret->type = ITYP_BOOL;
  ret->data.ui = !!v;
  ret->size = 0;
  ret->env = NULL;
}

void rain_set_str(box *ret, char* s) {
  ret->type = ITYP_STR;
  ret->data.s = s;
  ret->size = strlen(s);
  ret->env = NULL;
}

void rain_set_strcpy(box *ret, const char *s, int size) {
  ret->type = ITYP_STR;
  ret->data.s = GC_malloc(size + 1);
  ret->size = size;
  memcpy(ret->data.s, s, size);
  ret->data.s[size] = 0;
  ret->env = NULL;
}

void rain_set_table(box *ret) {
  table *arr = (table *)GC_malloc(sizeof(table));
  arr->cur = 0;
  arr->max = HASH_SIZE;
  arr->items = (item *)GC_malloc(sizeof(item) * HASH_SIZE);

  ret->type = ITYP_TABLE;
  ret->data.lpt = arr;
  ret->size = 0;
  ret->env = NULL;
}

void rain_set_func(box *ret, void *vp, int num_args) {
  ret->type = ITYP_FUNC;
  ret->data.vp = vp;
  ret->size = num_args;
  ret->env = NULL;
}

void rain_set_cdata(box *ret, void *vp) {
  ret->type = ITYP_CDATA;
  ret->data.vp = vp;
  ret->size = 0;
  ret->env = NULL;
}

void rain_set_env(box *val, box *env) {
  val->env = env;
}
