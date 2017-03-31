#include "rain.h"
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdlib.h>

void rain_ext_str_int(box *ret, box *value) {
  if(BOX_ISNT(value, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  // http://stackoverflow.com/questions/7021725/converting-string-to-integer-c
  char *end;
  char *start = value->data.s;
  if(start[0] == '\0' || isspace((unsigned char) start[0])) {
    return; // invalid
  }

  errno = 0;
  long res = strtol(start, &end, 10);
  if(res > INT_MAX || (errno == ERANGE && res == LONG_MAX)) {
    return; // overflow
  }
  if(res < INT_MIN || (errno == ERANGE && res == LONG_MIN)) {
    return; // underflow
  }
  if(end[0] != '\0') {
    return; // invalid
  }

  rain_set_int(ret, res);
}
