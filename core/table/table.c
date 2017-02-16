#include "../rain.h"
#include <gc.h>
#include <stdlib.h>
#include <string.h>


// table helpers

box* rain_new_table() {
  box* val = rain_box_malloc();
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

  if(BOX_IS(table, FUNC)) {
    rain_get(ret, table->env, key);
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

  rain_set_box(ret, &row->val);
}

void rain_put(box *table, box *key, box *val) {
  if(BOX_IS(table, FUNC)) {
    rain_put(table->env, key, val);
    return;
  }

  if(BOX_ISNT(table, TABLE)) {
    rain_throw(rain_exc_arg_mismatch);
  }

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

