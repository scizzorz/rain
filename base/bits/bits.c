#include "rain.h"

void rain_ext_lsh(box *ret, box *val, box *amt) {
  if(BOX_ISNT(val, INT) || BOX_ISNT(amt, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, val->data.si << amt->data.si);
}

void rain_ext_rsh(box *ret, box *val, box *amt) {
  if(BOX_ISNT(val, INT) || BOX_ISNT(amt, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, val->data.si >> amt->data.si);
}

void rain_ext_bor(box *ret, box *lhs, box *rhs) {
  if(BOX_ISNT(lhs, INT) || BOX_ISNT(rhs, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, lhs->data.si | rhs->data.si);
}

void rain_ext_band(box *ret, box *lhs, box *rhs) {
  if(BOX_ISNT(lhs, INT) || BOX_ISNT(rhs, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, lhs->data.si & rhs->data.si);
}

void rain_ext_bxor(box *ret, box *lhs, box *rhs) {
  if(BOX_ISNT(lhs, INT) || BOX_ISNT(rhs, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, lhs->data.si ^ rhs->data.si);
}

void rain_ext_bnot(box *ret, box *val) {
  if(BOX_ISNT(val, INT)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  rain_set_int(ret, ~(val->data.si));
}
