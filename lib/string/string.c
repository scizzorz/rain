#include <stdlib.h>
#include "string.h"


void rain_fmt(box *ret, box *val, box *fmt) {
  if(BOX_ISNT(fmt, STR)) {
    return;
  }

  switch(val->type) {
    case ITYP_INT:
      sprintf(fmt_buf, fmt->data.s, val->data.si);
      rain_set_strcpy(ret, fmt_buf, strlen(fmt_buf));
      break;

    case ITYP_FLOAT:
      sprintf(fmt_buf, fmt->data.s, val->data.f);
      rain_set_strcpy(ret, fmt_buf, strlen(fmt_buf));
      break;

    default:
      rain_to_string(ret, val);
  }
}

void rain_string_to_int(box *ret, box *str) {
  rain_set_int(ret, atoi(str->data.s));
}
