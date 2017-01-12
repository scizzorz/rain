#include "rain.h"

// system helpers

int rain_box_to_exit(box* val) {
  if(val->type == ITYP_NULL) {
    return val->data.ui;
  }
  else if(val->type == ITYP_BOOL) {
    return !(val->data.ui);
  }
  else if(val->type == ITYP_INT) {
    return val->data.ui;
  }
  else if(val->type == ITYP_FLOAT) {
    return (int)(val->data.f);
  }

  return 0;
}

void rain_print(box *val) {
  switch(val->type) {
    case ITYP_NULL:
      if(val->data.ui > 0) {
        printf("null(%lu)\n", val->data.ui);
        break;
      }

      printf("null\n");
      break;

    case ITYP_INT:
      printf("%lu\n", val->data.ui);
      break;

    case ITYP_FLOAT:
      printf("%f\n", val->data.f);
      break;

    case ITYP_BOOL:
      if(val->data.ui) {
        printf("true\n");
      }
      else {
        printf("false\n");
      }
      break;

    case ITYP_STR:
      printf("%.*s\n", val->size, val->data.s);
      break;

    case ITYP_TABLE:
      printf("table 0x%08lx\n", val->data.ui);
      break;

    case ITYP_FUNC:
      printf("func 0x%08lx\n", val->data.ui);
      break;

    case ITYP_DATA:
      printf("data 0x%08lx\n", val->data.ui);
      break;

    default:
      printf("???\n");
  }
}

// arithmetic

void rain_add(box *ret, box *lhs, box *rhs) {
  if(lhs->type == ITYP_INT && rhs->type == ITYP_INT) {
    ret->type = ITYP_INT;
    ret->data.ui = lhs->data.ui + rhs->data.ui;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_INT) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f + rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_INT && rhs->type == ITYP_FLOAT) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f + rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_FLOAT) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f + rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
}

void rain_sub(box *ret, box *lhs, box *rhs) {
  if(lhs->type == ITYP_INT && rhs->type == ITYP_INT) {
    ret->type = ITYP_INT;
    ret->data.ui = lhs->data.ui - rhs->data.ui;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_INT) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f - rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_INT && rhs->type == ITYP_FLOAT) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f - rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_FLOAT) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f - rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
}

void rain_mul(box *ret, box *lhs, box *rhs) {
  if(lhs->type == ITYP_INT && rhs->type == ITYP_INT) {
    ret->type = ITYP_INT;
    ret->data.ui = lhs->data.ui * rhs->data.ui;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_INT) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f * rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_INT && rhs->type == ITYP_FLOAT) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f * rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_FLOAT) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f * rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
}

void rain_div(box *ret, box *lhs, box *rhs) {
  if(lhs->type == ITYP_INT && rhs->type == ITYP_INT) {
    ret->type = ITYP_INT;
    ret->data.ui = lhs->data.ui / rhs->data.ui;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_INT) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f / rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_INT && rhs->type == ITYP_FLOAT) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f / rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_FLOAT) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f / rhs_f;
    ret->type = ITYP_FLOAT;
    ret->data.f = ret_f;
  }
}

// boolean binary operators

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

// TODO string comparisons

void rain_gt(box *ret, box *lhs, box *rhs) {
  if(lhs->type == ITYP_INT && rhs->type == ITYP_INT) {
    rain_set_bool(ret, lhs->data.si > rhs->data.si);
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_INT) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f + rhs_f;
    rain_set_bool(ret, lhs_f > rhs_f);
  }
  else if(lhs->type == ITYP_INT && rhs->type == ITYP_FLOAT) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f + rhs_f;
    rain_set_bool(ret, lhs_f > rhs_f);
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_FLOAT) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f + rhs_f;
    rain_set_bool(ret, lhs_f > rhs_f);
  }
}

void rain_ge(box *ret, box *lhs, box *rhs) {
  if(rain_hash_eq(lhs, rhs)) {
    rain_set_bool(ret, 1);
    return;
  }

  rain_gt(ret, lhs, rhs);
}

void rain_lt(box *ret, box *lhs, box *rhs) {
  if(lhs->type == ITYP_INT && rhs->type == ITYP_INT) {
    rain_set_bool(ret, lhs->data.si < rhs->data.si);
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_INT) {
    double lhs_f = lhs->data.f;
    double rhs_f = (double)rhs->data.si;
    double ret_f = lhs_f + rhs_f;
    rain_set_bool(ret, lhs_f < rhs_f);
  }
  else if(lhs->type == ITYP_INT && rhs->type == ITYP_FLOAT) {
    double lhs_f = (double)lhs->data.si;
    double rhs_f = lhs->data.f;
    double ret_f = lhs_f + rhs_f;
    rain_set_bool(ret, lhs_f < rhs_f);
  }
  else if(lhs->type == ITYP_FLOAT && rhs->type == ITYP_FLOAT) {
    double lhs_f = lhs->data.f;
    double rhs_f = rhs->data.f;
    double ret_f = lhs_f + rhs_f;
    rain_set_bool(ret, lhs_f < rhs_f);
  }
}

void rain_le(box *ret, box *lhs, box *rhs) {
  if(rain_hash_eq(lhs, rhs)) {
    rain_set_bool(ret, 1);
    return;
  }

  rain_lt(ret, lhs, rhs);
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
    case ITYP_NULL:
      return val->data.ui;
    case ITYP_INT:
      return val->data.ui;
    case ITYP_FLOAT:
      return val->data.ui;
    case ITYP_BOOL:
      return !!val->data.ui;
    case ITYP_STR:
      for(int i=0; i<val->size; i++) {
        hash += val->data.s[i];
      }
      return hash;
    case ITYP_TABLE:
      return val->data.ui;
    case ITYP_FUNC:
      return val->data.ui;
    case ITYP_DATA:
      return val->data.ui;
  }
  return 0;
}

unsigned char rain_hash_eq(box *one, box *two) {
  if(one->type != two->type) {
    return 0;
  }

  if(one->type == ITYP_STR) {
    return strcmp(one->data.s, two->data.s) == 0;
  }

  return one->data.ui == two->data.ui;
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

void rain_get(box *ret, box *table, box *key) {
  column *row = rain_has(table, key);

  if(row == NULL) {
    box mt_key;
    rain_set_str(&mt_key, "metatable");
    column* metatable = rain_has(table, &mt_key);
    if(metatable == NULL) {
      rain_set_null(ret);
      return;
    }

    rain_get(ret, &metatable->val, key);
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
  memcpy(ret->data.s, s, size + 1);
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

void rain_set_func(box *ret, void *vp) {
  ret->type = ITYP_FUNC;
  ret->data.vp = vp;
  ret->size = 0;
}

void rain_set_data(box *ret, void *vp) {
  ret->type = ITYP_DATA;
  ret->data.vp = vp;
  ret->size = 0;
}
