#include "rain.h"

void rain_ext_array_length(box *ret, box *val) {
  rain_set_int(ret, 0);
  box elem;
  box bnull;
  rain_set_null(&bnull);
  while(rain_has(val, ret)) {
    rain_get(&elem, val, ret);
    if (rain_hash_eq(&elem, &bnull)) {
      break;
    }
    ret->data.si++;
  }
}
