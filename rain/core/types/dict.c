#include "rain.h"
#include <stdio.h>

void rain_ext_dict_keys_iter(box *ret) {
  box key;

  // fetch the box that we're iterating
  rain_set_str(&key, "dict");
  box *dict = rain_get_ptr(ret, &key);

  // fetch the box that holds our position
  rain_set_str(&key, "cur");
  box *cur = rain_get_ptr(ret, &key);

  rain_set_null(ret);

  do {
    cur->data.si += 1;
    if(cur->data.si >= dict->data.lpt->max) {
      return;
    }
  } while(dict->data.lpt->items[cur->data.si] == NULL);

  rain_set_box(ret, &(dict->data.lpt->items[cur->data.si]->key));
}

void rain_ext_dict_keys(box *ret, box *val) {
  if(BOX_ISNT(val, TABLE)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  box key;
  box cur;

  box *env = rain_new_table();
  rain_set_func(ret, (void  *)(rain_ext_dict_keys_iter), 0);
  rain_set_env(ret, env);

  rain_set_str(&key, "cur");
  rain_set_int(&cur, -1);
  rain_put(env, &key, &cur);

  rain_set_str(&key, "dict");
  rain_put(env, &key, val);
}
