#include "rain.h"
#include <gc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


// system helpers

int rain_box_to_exit(box* val) {
  if(BOX_IS(val, NULL)) {
    return val->data.ui;
  }
  else if(BOX_IS(val, BOOL)) {
    return !(val->data.ui);
  }
  else if(BOX_IS(val, INT)) {
    return val->data.ui;
  }
  else if(BOX_IS(val, FLOAT)) {
    return (int)(val->data.f);
  }

  return 0;
}

void rain_check_callable(box *val, int num_args) {
  if(BOX_ISNT(val, FUNC)) {
    rain_panic(rain_exc_uncallable);
  }
  else if(val->size != num_args) {
    rain_panic(rain_exc_arg_mismatch);
  }
}

box *rain_box_malloc() {
  return (box *)GC_malloc(sizeof(box));
}
