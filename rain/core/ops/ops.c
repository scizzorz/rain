#include "rain.h"
#include <gc.h>
#include <string.h>


// magic methods

void rain_binary_magic(box *ret, box *lhs, box *rhs, char *meth) {
  box key;
  box val;
  rain_set_str(&key, meth);
  rain_set_null(&val);
  rain_get(&val, lhs->env, &key);

  rain_check_callable(&val, 2);

  void (*func_ptr)(box *, box *, box *) = (void (*)(box *, box *, box *))(val.data.vp);
  func_ptr(ret, lhs, rhs);
}


// unary

void rain_neg(box *ret, box *val) {
  if(BOX_IS(val, INT)) {
    rain_set_int(ret, -(val->data.si));
  }
  else if(BOX_IS(val, FLOAT)) {
    rain_set_float(ret, -(val->data.f));
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}

void rain_lnot(box *ret, box *val) {
  rain_set_bool(ret, !rain_truthy(val));
}


// arithmetic

void rain_add(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_int(ret, lhs->data.si + rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_float(ret, lhs_f + rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f + rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f + rhs_f);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "add");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}

void rain_sub(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_int(ret, lhs->data.si - rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_float(ret, lhs_f - rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f - rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f - rhs_f);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "sub");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}

void rain_mul(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_int(ret, lhs->data.si * rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_float(ret, lhs_f * rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f * rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f * rhs_f);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "mul");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}

void rain_div(box *ret, box *lhs, box *rhs) {
  // probably best to catch div by zero errors as SIG_FPE somehow?
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_int(ret, lhs->data.si / rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_float(ret, lhs_f / rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f / rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_float(ret, lhs_f / rhs_f);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "div");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}


// boolean
// NOTE: these aren't actually used by the | and & operators

unsigned char rain_truthy(box *val) {
  return (val->type != ITYP_NULL) && (val->data.ui != 0);
}

void rain_ext_truthy(box *ret, box *val) {
  rain_set_bool(ret, rain_truthy(val));
}

void rain_and(box *ret, box *lhs, box *rhs) {
  if(!rain_truthy(lhs)) {
    rain_set_box(ret, lhs);
    return;
  }

  rain_set_box(ret, rhs);
}

void rain_or(box *ret, box *lhs, box *rhs) {
  if(rain_truthy(lhs)) {
    rain_set_box(ret, lhs);
    return;
  }

  rain_set_box(ret, rhs);
}


// comparison

void rain_eq(box *ret, box *lhs, box *rhs) {
  rain_set_bool(ret, rain_hash_eq(lhs, rhs));
}

void rain_ne(box *ret, box *lhs, box *rhs) {
  rain_set_bool(ret, !rain_hash_eq(lhs, rhs));
}

void rain_gt(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_bool(ret, lhs->data.si > rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_bool(ret, lhs_f > rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f > rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f > rhs_f);
  }
  else if(BOX_IS(lhs, STR) && BOX_IS(rhs, STR)) {
    char *lhs_s = lhs->data.s;
    char *rhs_s = rhs->data.s;
    rain_set_bool(ret, strcmp(lhs_s, rhs_s) > 0);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "gt");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}

void rain_ge(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_bool(ret, lhs->data.si >= rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_bool(ret, lhs_f >= rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f >= rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f >= rhs_f);
  }
  else if(BOX_IS(lhs, STR) && BOX_IS(rhs, STR)) {
    char *lhs_s = lhs->data.s;
    char *rhs_s = rhs->data.s;
    rain_set_bool(ret, strcmp(lhs_s, rhs_s) >= 0);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "ge");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}

void rain_lt(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_bool(ret, lhs->data.si < rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_bool(ret, lhs_f < rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f < rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f < rhs_f);
  }
  else if(BOX_IS(lhs, STR) && BOX_IS(rhs, STR)) {
    char *lhs_s = lhs->data.s;
    char *rhs_s = rhs->data.s;
    rain_set_bool(ret, strcmp(lhs_s, rhs_s) < 0);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "lt");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}

void rain_le(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    rain_set_bool(ret, lhs->data.si <= rhs->data.si);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    rain_set_bool(ret, lhs_f <= rhs_f);
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f <= rhs_f);
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    rain_set_bool(ret, lhs_f <= rhs_f);
  }
  else if(BOX_IS(lhs, STR) && BOX_IS(rhs, STR)) {
    char *lhs_s = lhs->data.s;
    char *rhs_s = rhs->data.s;
    rain_set_bool(ret, strcmp(lhs_s, rhs_s) <= 0);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "le");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}


// string concat

void rain_string_concat(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, STR) && BOX_IS(rhs, STR)) {
    int length = lhs->size + rhs->size;
    char *cat = GC_malloc(length + 1);

    strcat(cat, lhs->data.s);
    strcat(cat + lhs->size, rhs->data.s);

    rain_set_str(ret, cat);
  }
  else if(BOX_IS(lhs, TABLE) && BOX_IS(rhs, TABLE)) {
    rain_binary_magic(ret, lhs, rhs, "concat");
  }
  else {
    rain_panic(rain_exc_arg_mismatch);
  }
}
