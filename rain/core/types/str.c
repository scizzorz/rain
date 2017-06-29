#include "rain.h"
#include <gc.h>
#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>

box *rain_exc_str_fmt_error;

void rain_ext_str_length(box *ret, box *val) {
  rain_set_int(ret, val->size);
}

void rain_ext_str_int(box *ret, box *val) {
  if(BOX_ISNT(val, STR)) {
    rain_panic(rain_exc_arg_mismatch);
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
    rain_panic(rain_exc_arg_mismatch);
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

void rain_ext_str_fmt(box *ret, box *fmt, box *args) {
  int start = 0;
  int in = 0;
  int out = 0;
  int ins = fmt->size;
  int outs = ins * 2; // start with twice the size
  int counter = 0;

  char *str = fmt->data.s;
  char *new = GC_malloc(outs);

  box key;
  box val;

  while(1) {
    // reached end of input
    if(in >= ins) {
      break;
    }

    // found a starting {
    if(str[in] == '{') {
      in++;

      // find a matching }
      start = in;
      while(in < ins && str[in] != '}') {
        in++;
      }

      // reached EOS without finding a matching }
      if(in == ins) {
        rain_panic(rain_exc_str_fmt_error);
      }

      else {
        // check for empty key
        if(in == start) {
          rain_set_int(&key, counter);
          counter++;
        }
        else {
          // read the key as a string
          rain_set_strcpy(&key, str + start, in - start);

          // convert the string to an int if possible
          // by passing in &key as the ret value as well, it will
          // remain unchanged unless the conversion is successful
          rain_ext_str_int(&key, &key);
        }
        rain_set_null(&val);
        rain_set_null(ret);

        // read the key out of the arg table and coerce it
        rain_get(&val, args, &key);
        rain_ext_to_str(ret, &val);

        // resize if needed
        if(out + ret->size >= outs) {
          outs *= 2;
          new = GC_realloc(new, outs);
        }

        // copy output string
        strcpy(new + out, ret->data.s);
        out += ret->size;
        in++;
      }
    }

    // just copy one character
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

void rain_ext_str_char_at(box *ret, box *val, box *key) {
  if(BOX_ISNT(val, STR)) {
    rain_panic(rain_exc_arg_mismatch);
  }

  // pass non-int keys up to the metatable
  if(BOX_ISNT(key, INT)) {
    if(rain_has_meta(val)) {
      rain_get(ret, val->env, key);
      return;
    }
  }

  // positive ints
  if(key->data.si >= 0 && key->data.si < val->size) {
    rain_set_strcpy(ret, val->data.s + key->data.si, 1);
  }

  // negative ints
  else if(key->data.si < 0 && key->data.si >= -(val->size)) {
    rain_set_strcpy(ret, val->data.s + val->size + key->data.si, 1);
  }
}
