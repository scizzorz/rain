#include "rain.h"
#include <gc.h>
#include <stdlib.h>
#include <string.h>


// table helpers

box* rain_new_table() {
  box* val = rain_box_malloc();
  rain_set_table(val);
  return val;
}

unsigned long rain_hash(box *val) {
  unsigned int hash = 5381;

  switch(val->type) {
    case ITYP_BOOL:
      return !!val->data.ui;
    case ITYP_STR:
      for(int i=0; i<val->size; i++) {
        hash += (hash << 5) + val->data.s[i];
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

item *rain_has(box *tab, box *key) {
  int cur = tab->data.lpt->cur;
  int max = tab->data.lpt->max;
  item **items = tab->data.lpt->items;
  unsigned long key_hash = rain_hash(key);

  while(1) {
    if(items[key_hash % max] == NULL) {
      return NULL;
    }

    if(rain_hash_eq(key, &(items[key_hash % max]->key))) {
      break;
    }

    key_hash += 1;
  }

  return items[key_hash % max];
}

box *rain_get_ptr(box *tab, box *key) {
  item *ptr = rain_has(tab, key);
  if(ptr == NULL) {
    return NULL;
  }
  return &ptr->val;
}

void rain_get(box *ret, box *tab, box *key) {
  box index_key;
  box index_func;

  if(rain_has_meta(tab)) {
    rain_set_str(&index_key, "get");
    rain_set_null(&index_func);
    rain_get(&index_func, tab->env, &index_key);

    if(BOX_IS(&index_func, FUNC) && index_func.size == 2) {
      void (*func_ptr)(box *, box *, box *) = (void (*)(box *, box *, box *))(index_func.data.vp);
      if(rain_has_meta(&index_func)) {
        rain_set_box(ret, index_func.env);
      }

      func_ptr(ret, tab, key);
      return;
    }
  }

  if(BOX_IS(tab, TABLE)) {
    item *row = rain_has(tab, key);
    if(row != NULL) {
      rain_set_box(ret, &row->val);
      return;
    }
  }

  if(rain_has_meta(tab)) {
    rain_get(ret, tab->env, key);
    return;
  }
}

void rain_put(box *tab, box *key, box *val) {
  box index_ret;
  box index_key;
  box index_func;

  if(rain_has_meta(tab)) {
    rain_set_null(&index_ret);
    rain_set_str(&index_key, "set");
    rain_set_null(&index_func);
    rain_get(&index_func, tab->env, &index_key);

    if(BOX_IS(&index_func, FUNC) && index_func.size == 3) {
      void (*func_ptr)(box *, box *, box *, box *) = (void (*)(box *, box *, box *, box *))(index_func.data.vp);
      if(rain_has_meta(&index_func)) {
        rain_set_box(&index_ret, index_func.env);
      }

      func_ptr(&index_ret, tab, key, val);
      return;
    }
  }

  if(BOX_IS(tab, FUNC) && rain_has_meta(tab)) {
    rain_put(tab->env, key, val);
    return;
  }

  if(BOX_ISNT(tab, TABLE)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  rain_put_aux(tab, key, val, NULL);
}

void rain_put_aux(box *tab, box *key, box *val, item *pair) {
  int cur = tab->data.lpt->cur;
  int max = tab->data.lpt->max;
  item **items = tab->data.lpt->items;
  unsigned long key_hash = rain_hash(key);

  while(1) {
    if(items[key_hash % max] == NULL) {
      if(pair == NULL) {
        items[key_hash % max] = GC_malloc(sizeof(item));
      }
      else {
        items[key_hash % max] = pair;
      }

      items[key_hash % max]->key = *key;
      items[key_hash % max]->val = *val;
      tab->data.lpt->cur += 1;
      cur += 1;
      break;
    }

    if(rain_hash_eq(&(items[key_hash % max]->key), key)) {
      items[key_hash % max]->val = *val;
      break;
    }

    key_hash += 1;
  }

  if(cur > max / 2) {
    tab->data.lpt->cur = 0;
    tab->data.lpt->max = max * 2;
    tab->data.lpt->items = (item **)GC_malloc(sizeof(item*) * max * 2);

    for(int i=0; i<max; i++) {
      if(items[i] != NULL) {
        rain_put_aux(tab, &(items[i]->key), &(items[i]->val), items[i]);
      }
    }
  }
}

void rain_ext_get(box *ret, box *tab, box *key) {
  box clone;
  rain_set_box(&clone, tab);
  clone.env = NULL;
  rain_get(ret, &clone, key);
}

void rain_ext_set(box *ret, box *tab, box *key, box *val) {
  box clone;
  rain_set_box(&clone, tab);
  clone.env = NULL;

  rain_put(&clone, key, val);
}
