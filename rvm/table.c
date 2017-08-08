#include "rain.h"

#include <string.h>

uint64_t R_hash(R_box *val) {
  uint64_t hash = 5381;

  switch(val->type) {
    case R_TYPE_BOOL:
      return !!val->u64;
    case R_TYPE_STR:
      for(int i=0; i<val->size; i++) {
        hash += (hash << 5) + val->str[i];
      }
      return hash;
  }

  return (val->u64 << 5) + 5381; // lol?
}

bool R_hash_eq(R_box *lhs, R_box *rhs) {
  if(lhs->type != rhs->type) {
    return false;
  }

  if(R_TYPE_IS(lhs, STR)) {
    return strcmp(lhs->str, rhs->str) == 0;
  }

  return lhs->u64 == rhs->u64;
}

void R_table_clone(R_box *from, R_box *to) {
  uint32_t max = from->table->max;
  R_item **items = from->table->items;

  R_set_table_sized(to, max);
  to->meta = from->meta;

  for(int i=0; i<max; i++) {
    if(items[i] != NULL) {
      R_table_set_aux(to, &items[i]->key, &items[i]->val, items[i]);
    }
  }
}

R_item *R_table_get_item(R_box *table, R_box *key) {
  uint32_t cur = table->table->cur;
  uint32_t max = table->table->max;
  R_item **items = table->table->items;
  uint64_t key_hash = R_hash(key);
  uint64_t idx = key_hash % max;

  while(1) {
    if(items[idx] == NULL) {
      return NULL;
    }

    if(items[idx]->hash == key_hash && R_hash_eq(key, &items[idx]->key)) {
      break;
    }

    idx = (idx + 1) % max;
  }

  return items[idx];
}

R_box *R_table_get(R_box *table, R_box *key) {
  R_item *item = R_table_get_item(table, key);

  if(item == NULL) {
    return NULL;
  }

  return &item->val;
}

void R_table_set(R_box *table, R_box *key, R_box *val) {
  R_table_set_aux(table, key, val, NULL);
}

void R_table_set_aux(R_box *table, R_box *key, R_box *val, R_item *item) {
  uint32_t cur = table->table->cur;
  uint32_t max = table->table->max;
  R_item **items = table->table->items;
  uint64_t key_hash = R_hash(key);
  uint64_t idx = key_hash % max;

  while(1) {
    if(items[idx] == NULL) {
      items[idx] = (item == NULL) ? GC_malloc(sizeof(R_item)) : item;
      items[idx]->hash = key_hash;
      items[idx]->key = *key;
      items[idx]->val = *val;
      table->table->cur += 1;
      cur += 1;
      break;
    }

    if(items[idx]->hash == key_hash && R_hash_eq(key, &items[idx]->key)) {
      items[idx]->val = *val;
      break;
    }

    idx = (idx + 1) % max;
  }

  if(cur > max / 2) {
    table->table->cur = 0;
    table->table->max *= 2;
    table->table->items = GC_malloc(sizeof(R_item *) * max * 2);

    for(int i=0; i<max; i++) {
      if(items[i] != NULL) {
        R_table_set_aux(table, &items[i]->key, &items[i]->val, items[i]);
      }
    }
  }
}
