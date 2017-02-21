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
  int searches = 0;
  int size = table->size;
  unsigned long key_hash = rain_hash(key);
  column **dict = table->data.t;
  column *row = dict[key_hash % size];

  if(row == NULL) {
    return NULL;
  }

  while(!rain_hash_eq(key, &row->key)) {
    searches += 1;
    if(searches == size) {
      return NULL;
    }

    key_hash += 1;
    row = dict[key_hash % size];
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

  if(BOX_IS(table, TABLE)) {
    column *row = rain_has(table, key);
    if(row != NULL) {
      rain_set_box(ret, &row->val);
      return;
    }
  }

  if(table->env != NULL) {
    rain_get(ret, table->env, key);
    return;
  }
}

void rain_put(box *table, box *key, box *val) {
  if(BOX_IS(table, FUNC)) {
    rain_put(table->env, key, val);
    return;
  }

  if(BOX_ISNT(table, TABLE)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  int used = 0;
  int size = table->size;
  unsigned long key_hash = rain_hash(key) % size;
  column **dict = table->data.t;
  column **rowp = dict + (key_hash % size);

  while(1) {
    if(*rowp == NULL) { // new pair
      *rowp = rain_new_pair(key, val);
      break;
    }
    else if(rain_hash_eq(&(*rowp)->key, key)) { // update
      (*rowp)->val = *val;
      break;
    }

    used += 1;
    if(used >= size / 2) {
      break;
    }

    key_hash += 1;
    rowp = dict + (key_hash % size);
  }

  used = 0;
  for(int i=0; i<size; i++) {
    if(dict[i] != NULL) {
      used += 1;
    }
  }

  if(used >= size / 2) {
    table->size *= 2;

    column **new_arr = (column **)GC_malloc(sizeof(column *) * table->size);
    table->data.t = new_arr; // dict still points to old array

    rain_put(table, key, val);
    rain_print(key);
    for(int i=0; i<size; i++) {
      if(dict[i] != NULL) {
        rain_print(&dict[i]->key);
        rain_put(table, &dict[i]->key, &dict[i]->val);
      }
    }

    GC_free((void *)dict);

  }
}

