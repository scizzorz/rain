#include "rain.h"
#include <math.h>

void rain_ext_float_int(box *ret, box *value) {
  if(BOX_ISNT(value, FLOAT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)value->data.f);
}


void rain_ext_float_floor(box *ret, box *value) {
  if(BOX_ISNT(value, FLOAT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)floor(value->data.f));
}

void rain_ext_float_round(box *ret, box *value) {
  if(BOX_ISNT(value, FLOAT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)round(value->data.f));
}

void rain_ext_float_ceil(box *ret, box *value) {
  if(BOX_ISNT(value, FLOAT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, (signed long)ceil(value->data.f));
}

void rain_ext_float_abs(box *ret, box *value) {
  if(BOX_ISNT(value, FLOAT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_float(ret, fabs(value->data.f));
}
