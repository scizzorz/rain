#include "rain.h"
#include <gc.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

box *rain_exc_str_fmt_error;

void rain_ext_str_int(box *ret, box *val) {
  if(BOX_ISNT(val, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  // http://stackoverflow.com/questions/7021725/converting-string-to-integer-c
  char *end;
  char *start = val->data.s;
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

void rain_ext_str_float(box *ret, box *val) {
  if(BOX_ISNT(val, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  char *end;
  char *start = val->data.s;
  if(start[0] == '\0' || isspace((unsigned char) start[0])) {
    return; // invalid
  }

  errno = 0;
  double res = strtod(start, &end);
  if(errno == ERANGE) {
    return; // out of range?
  }

  if(end[0] != '\0') {
    return; // invalid
  }

  rain_set_float(ret, res);
}

void rain_ext_str_fmt(box *ret, box *val, box *args) {
  int start = 0;
  int in = 0;
  int out = 0;
  int ins = val->size;
  int outs = ins * 2; // start with twice the size

  char *str = val->data.s;
  char *new = GC_malloc(outs);
  char *write = NULL;

  box key;

  while(1) {
    write = NULL;
    if(in >= ins) {
      break;
    }

    if(str[in] == '{') {
      in++;

      start = in;
      while(in < ins && str[in] != '}') {
        in++;
      }

      if(in == ins) {
        rain_throw(rain_exc_str_fmt_error);
      }
      else {
        rain_set_strcpy(&key, str + start, in - start);
        rain_get(ret, args, &key);

        if(out + ret->size >= outs) {
          outs *= 2;
          new = GC_realloc(new, outs);
        }

        strcpy(new + out, ret->data.s);
        out += ret->size;
        in++;
      }
    }
    else {
      if(out >= outs) {
        outs *= 2;
        new = GC_realloc(new, outs);
      }

      new[out] = str[in];
      out++;
      in++;
    }
  }

  rain_set_strcpy(ret, new, out);
  GC_free(new);
}
