#include "rain.h"

void rain_ext_array_length(box *ret, box *val) {
  rain_set_int(ret, 0);
  while(rain_has(val, ret)) {
    ret->data.si++;
  }
}
