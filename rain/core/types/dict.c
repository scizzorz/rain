#include "rain.h"
#include <stdio.h>

item *rain_dict_iter(box *env) {
  box key;

  // fetch the box that we're iterating
  rain_set_str(&key, "dict");
  box *dict = rain_get_ptr(env, &key);

  // fetch the box that holds our position
  rain_set_str(&key, "cur");
  box *cur = rain_get_ptr(env, &key);

  do {
    cur->data.si += 1;
    if(cur->data.si >= dict->data.lpt->max) {
      return NULL;
    }
  } while(dict->data.lpt->items[cur->data.si] == NULL);

  return dict->data.lpt->items[cur->data.si];
}

void rain_ext_dict_keys_iter(box *ret) {
  item *pair = rain_dict_iter(ret);
  if(pair == NULL) {
    rain_set_null(ret);
  }
  else {
    rain_set_box(ret, &(pair->key));
  }
}

void rain_ext_dict_values_iter(box *ret) {
  item *pair = rain_dict_iter(ret);
  if(pair == NULL) {
    rain_set_null(ret);
  }
  else {
    rain_set_box(ret, &(pair->val));
  }
}
