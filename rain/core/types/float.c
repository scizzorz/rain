#include "rain.h"
#include <gc.h>
#include <math.h>
#include <stdio.h>

void rain_ext_float_int(box *ret, box *val) {
  if(BOX_ISNT(val, FLOAT)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)val->data.f);
}


void rain_ext_float_floor(box *ret, box *val) {
  if(BOX_ISNT(val, FLOAT)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)floor(val->data.f));
}

void rain_ext_float_round(box *ret, box *val) {
  if(BOX_ISNT(val, FLOAT)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)round(val->data.f));
}

void rain_ext_float_ceil(box *ret, box *val) {
  if(BOX_ISNT(val, FLOAT)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)ceil(val->data.f));
}

void rain_ext_float_abs(box *ret, box *val) {
  if(BOX_ISNT(val, FLOAT)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  rain_set_float(ret, fabs(val->data.f));
}

void rain_ext_float_str(box *ret, box *val) {
  if(BOX_ISNT(val, FLOAT)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  char strbuf[24];
  int len = snprintf(strbuf, 24, "%f", val->data.f);
  if(len < 24) { // it fit in our buffer
    rain_set_strcpy(ret, strbuf, len);
  }
  else { // we need to malloc a big enough buffer
    char *newbuf = GC_malloc(len + 1);
    sprintf(newbuf, "%f", val->data.f);
    rain_set_str(ret, newbuf);
  }
}
