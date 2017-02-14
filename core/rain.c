#include "rain.h"
#include "except/except.h"
#include "env/env.h"

// system helpers

void rain_main(box *ret, box *func) {
  void (*func_ptr)(box *) = (void (*)(box *))(func->data.vp);
  func_ptr(ret);
}

int rain_box_to_exit(box* val) {
  if(BOX_IS(val, NULL)) {
    return val->data.ui;
  }
  else if(BOX_IS(val, BOOL)) {
    return !(val->data.ui);
  }
  else if(BOX_IS(val, INT)) {
    return val->data.ui;
  }
  else if(BOX_IS(val, FLOAT)) {
    return (int)(val->data.f);
  }

  return 0;
}

void rain_print(box *val) {
  box ret;
  rain_to_string(&ret, val);
  printf("%.*s\n", ret.size, ret.data.s);
}

void rain_ext_print(box *ret, box *val) {
  rain_print(val);
}

void rain_exit(box *ret, box *val) {
  exit(rain_box_to_exit(val));
}

// unary operators

void rain_neg(box *ret, box *val) {
  if(BOX_IS(val, INT)) {
    rain_set_int(ret, -(val->data.si));
  }
  else if(BOX_IS(val, FLOAT)) {
    rain_set_float(ret, -(val->data.f));
  }
  else {
    rain_throw(rain_exc_arg_mismatch);
  }
}

void rain_not(box *ret, box *val) {
  rain_set_bool(ret, !rain_truthy(val));
}

// arithmetic

void rain_add(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    ret->type = ITYP_INT;
    ret->data.si = lhs->data.si + rhs->data.si;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f + rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f + rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f + rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else {
    rain_throw(rain_exc_arg_mismatch);
  }
}

void rain_sub(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    ret->type = ITYP_INT;
    ret->data.si = lhs->data.si - rhs->data.si;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f - rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f - rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f - rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else {
    rain_throw(rain_exc_arg_mismatch);
  }
}

void rain_mul(box *ret, box *lhs, box *rhs) {
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    ret->type = ITYP_INT;
    ret->data.si = lhs->data.si * rhs->data.si;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f * rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f * rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f * rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else {
    rain_throw(rain_exc_arg_mismatch);
  }
}

void rain_div(box *ret, box *lhs, box *rhs) {
  // probably best to catch div by zero errors as SIG_FPE somehow?
  if(BOX_IS(lhs, INT) && BOX_IS(rhs, INT)) {
    ret->type = ITYP_INT;
    ret->data.si = lhs->data.si / rhs->data.si;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, INT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f / rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, INT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f / rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(BOX_IS(lhs, FLOAT) && BOX_IS(rhs, FLOAT)) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f / rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else {
    rain_throw(rain_exc_arg_mismatch);
  }
}

// boolean binary operators
// NOTE: these aren't actually used by the | and & operators

unsigned char rain_truthy(box *val) {
  return (val->type != ITYP_NULL) && (val->data.ui != 0);
}

void rain_and(box *ret, box *lhs, box *rhs) {
  if(!rain_truthy(lhs)) {
    ret->type = lhs->type;
    ret->data.ui = lhs->data.ui;
    ret->size = lhs->size;
    return;
  }

  ret->type = rhs->type;
  ret->data.ui = rhs->data.ui;
  ret->size = rhs->size;
}

void rain_or(box *ret, box *lhs, box *rhs) {
  if(rain_truthy(lhs)) {
    ret->type = lhs->type;
    ret->data.ui = lhs->data.ui;
    ret->size = lhs->size;
    return;
  }

  ret->type = rhs->type;
  ret->data.ui = rhs->data.ui;
  ret->size = rhs->size;
}

// comparison operators

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
}

// string helpers

void rain_string_concat(box *ret, box *lhs, box *rhs) {
  if(BOX_ISNT(lhs, STR) && BOX_ISNT(rhs, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }
  else if(BOX_ISNT(rhs, STR)) {
    rain_set_box(ret, lhs);
  }
  else if(BOX_ISNT(lhs, STR)) {
    rain_set_box(ret, rhs);
  }
  else {
    int length = lhs->size + rhs->size;
    char *cat = GC_malloc(length + 1);

    strcat(cat, lhs->data.s);
    strcat(cat + lhs->size, rhs->data.s);

    rain_set_strcpy(ret, cat, length);
  }
}

void rain_to_string(box *ret, box *val) {
  box key;
  box to_str;

  switch(val->type) {
    case ITYP_NULL:
      rain_set_str(ret, "null");
      break;

    case ITYP_INT:
      sprintf(rain_to_str_buf, "%ld", val->data.si);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_FLOAT:
      sprintf(rain_to_str_buf, "%f", val->data.f);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_BOOL:
      rain_set_str(ret, val->data.ui ? "true" : "false");
      break;

    case ITYP_STR:
      rain_set_strcpy(ret, val->data.s, val->size);
      break;

    case ITYP_TABLE:
      rain_set_str(&key, "_str");
      rain_get(&to_str, val, &key);
      if(BOX_IS(&to_str, FUNC) && to_str.size == 1) {
        void (*func_ptr)(box *, box *) = (void (*)(box *, box *))(to_str.data.vp);
        func_ptr(ret, val);
        break;
      }

      sprintf(rain_to_str_buf, "table 0x%08lx", val->data.ui);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_FUNC:
      sprintf(rain_to_str_buf, "func 0x%08lx + %08lx", val->data.ui, (unsigned long)(val->env));
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_CDATA:
      sprintf(rain_to_str_buf, "cdata 0x%08lx", val->data.ui);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;
  }
}

// table helpers

box* rain_new_table() {
  box* val = (box *)GC_malloc(sizeof(box));
  rain_set_table(val);
  return val;
}

column *rain_new_pair(box *key, box *val) {
  column *ret = (column *)GC_malloc(sizeof(column));
  ret->key = *key;
  ret->val = *val;
  ret->next = NULL;
  return ret;
}

unsigned long rain_hash(box *val) {
  unsigned int hash = 0;
  switch(val->type) {
    case ITYP_BOOL:
      return !!val->data.ui;
    case ITYP_STR:
      for(int i=0; i<val->size; i++) {
        hash += val->data.s[i];
      }
      return hash;
  }

  return val->data.ui;
}

unsigned char rain_hash_eq(box *one, box *two) {
  if(one->type != two->type) {
    return 0;
  }

  if(BOX_IS(one, STR)) {
    return strcmp(one->data.s, two->data.s) == 0;
  }

  return one->data.ui == two->data.ui;
}

int rain_array_length(box *table) {
  int length = 0;
  box i_box;

  rain_set_int(&i_box, 0);
  while(rain_has(table, &i_box)) {
    i_box.data.si++;
  }

  return i_box.data.si;
}

column *rain_has(box *table, box *key) {
  unsigned long key_hash = rain_hash(key) % HASH_SIZE;
  column **dict = table->data.t;
  column *row = dict[key_hash];

  if(row == NULL) {
    return NULL;
  }

  while(!rain_hash_eq(key, &row->key)) {
    row = row->next;
    if(row == NULL) {
      return NULL;
    }
  }

  return row;
}

box *rain_get_ptr(box *table, box *key) {
  column *ptr = rain_has(table, key);
  return &(ptr->val);
}

void rain_get(box *ret, box *table, box *key) {
  if(BOX_IS(table, STR) && BOX_IS(key, INT)) {
    if(key->data.si >= 0 && key->data.si < table->size) {
      rain_set_strcpy(ret, table->data.s + key->data.si, 1);
    }
    else if(key->data.si < 0 && key->data.si >= -(table->size)) {
      rain_set_strcpy(ret, table->data.s + table->size + key->data.si, 1);
    }
    return;
  }
  if(BOX_ISNT(table, TABLE)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  column *row = rain_has(table, key);

  if(row == NULL) {
    box mt_key;
    rain_set_str(&mt_key, "metatable");
    column* metatable = rain_has(table, &mt_key);
    if(metatable == NULL) {
      rain_set_null(ret);
      return;
    }

    if(BOX_IS(&metatable->val, TABLE) && (&metatable->val) != table) {
      rain_get(ret, &metatable->val, key);
    }
    return;
  }

  ret->type = row->val.type;
  ret->data.ui = row->val.data.ui;
  ret->size = row->val.size;
}

void rain_put(box *table, box *key, box *val) {
  unsigned long key_hash = rain_hash(key) % HASH_SIZE;
  column **dict = table->data.t;
  column **row = dict + key_hash;
  while(1) {
    if(*row == NULL) { // new pair
      *row = rain_new_pair(key, val);
      return;
    }
    else if(rain_hash_eq(&(*row)->key, key)) { // update
      (*row)->val = *val;
      return;
    }
    row = &((*row)->next);
  }
}

// string AND table helpers

void rain_length(box *ret, box *val) {
  if(BOX_IS(val, STR) || BOX_IS(val, FUNC)) {
    rain_set_int(ret, val->size);
  }
  else if(BOX_IS(val, TABLE)) {
    rain_set_int(ret, rain_array_length(val));
  }
}

void rain_type(box *ret, box *val) {
  rain_set_int(ret, val->type);
}

// box helpers

void rain_set_box(box *ret, box *from) {
  ret->type = from->type;
  ret->data.ui = from->data.ui;
  ret->size = from->size;
}

void rain_set_null(box *ret) {
  ret->type = ITYP_NULL;
  ret->data.ui = 0;
  ret->size = 0;
}

void rain_set_int(box *ret, signed long si) {
  ret->type = ITYP_INT;
  ret->data.si = si;
  ret->size = 0;
}

void rain_set_float(box *ret, double f) {
  ret->type = ITYP_FLOAT;
  ret->data.f = f;
  ret->size = 0;
}

void rain_set_bool(box *ret, unsigned char v) {
  ret->type = ITYP_BOOL;
  ret->data.ui = !!v;
  ret->size = 0;
}

void rain_set_str(box *ret, char* s) {
  ret->type = ITYP_STR;
  ret->data.s = s;
  ret->size = strlen(s);
}

void rain_set_strcpy(box *ret, const char *s, int size) {
  ret->type = ITYP_STR;
  ret->data.s = GC_malloc(size + 1);
  ret->size = size;
  memcpy(ret->data.s, s, size);
  ret->data.s[size] = 0;
}

void rain_set_table(box *ret) {
  column **arr = (column **)GC_malloc(sizeof(column *) * HASH_SIZE);
  for(int i=0; i<HASH_SIZE; i++) {
    arr[i] = NULL;
  }

  ret->type = ITYP_TABLE;
  ret->data.t = arr;
  ret->size = 0;
}

void rain_set_func(box *ret, void *vp, int num_args) {
  ret->type = ITYP_FUNC;
  ret->data.vp = vp;
  ret->size = num_args;
}

void rain_set_cdata(box *ret, void *vp) {
  ret->type = ITYP_CDATA;
  ret->data.vp = vp;
  ret->size = 0;
}
