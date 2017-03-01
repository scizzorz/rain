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
  item *items = tab->data.lpt->items;
  unsigned long key_hash = rain_hash(key);

  while(1) {
    if(!items[key_hash % max].valid) {
      return NULL;
    }

    if(rain_hash_eq(key, &(items[key_hash % max].key))) {
      break;
    }

    key_hash += 1;
  }

  return items + (key_hash % max);
}

box *rain_get_ptr(box *tab, box *key) {
  item *ptr = rain_has(tab, key);
  return &ptr->val;
}

void rain_get(box *ret, box *tab, box *key) {
  if(BOX_IS(tab, STR) && BOX_IS(key, INT)) {
    if(key->data.si >= 0 && key->data.si < tab->size) {
      rain_set_strcpy(ret, tab->data.s + key->data.si, 1);
    }
    else if(key->data.si < 0 && key->data.si >= -(tab->size)) {
      rain_set_strcpy(ret, tab->data.s + tab->size + key->data.si, 1);
    }
    return;
  }

  if(BOX_IS(tab, TABLE)) {
    item *row = rain_has(tab, key);
    if(row != NULL) {
      rain_set_box(ret, &row->val);
      return;
    }
  }

  if(tab->env != NULL) {
    rain_get(ret, tab->env, key);
    return;
  }
}

void rain_put(box *tab, box *key, box *val) {
  if(BOX_IS(tab, FUNC)) {
    rain_put(tab->env, key, val);
    return;
  }

  if(BOX_ISNT(tab, TABLE)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  int cur = tab->data.lpt->cur;
  int max = tab->data.lpt->max;
  item *items = tab->data.lpt->items;
  unsigned long key_hash = rain_hash(key);

  while(1) {
    if(!items[key_hash % max].valid) {
      items[key_hash % max].valid = 1;
      items[key_hash % max].key = *key;
      items[key_hash % max].val = *val;
      tab->data.lpt->cur += 1;
      cur += 1;
      break;
    }

    if(rain_hash_eq(&(items[key_hash % max].key), key)) {
      items[key_hash % max].val = *val;
      break;
    }

    key_hash += 1;
  }

  if(cur > max / 2) {
    tab->data.lpt->cur = 0;
    tab->data.lpt->max = max * 2;
    tab->data.lpt->items = (item *)GC_malloc(sizeof(item) * max * 2);

    for(int i=0; i<max; i++) {
      if(items[i].valid) {
        rain_put(tab, &items[i].key, &items[i].val);
      }
    }

    GC_free((void *)items);

  }
}

