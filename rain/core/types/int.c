#include "rain.h"
#include <stdlib.h>
#include <stdio.h>

void rain_ext_int_float(box *ret, box *val) {
  if(BOX_ISNT(val, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_float(ret, (double)val->data.si);
}

void rain_ext_int_abs(box *ret, box *val) {
  if(BOX_ISNT(val, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, labs(val->data.si));
}

void rain_ext_int_str(box *ret, box *val) {
  if(BOX_ISNT(val, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  char strbuf[24]; // 20 should be the longest, but we'll play it safe
  int len = sprintf(strbuf, "%ld", val->data.si);
  rain_set_strcpy(ret, strbuf, len);
}
