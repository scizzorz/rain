#include "rain.h"
#include <gc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


// system helpers

void rain_main(box *ret, box *func) {
  void (*func_ptr)(box *) = (void (*)(box *))(func->data.vp);
  func_ptr(ret);
}

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

void rain_print(box *val) {
  if(BOX_IS(val, STR)) {
    printf("%.*s\n", val->size, val->data.s);
  }
  else {
    box ret;
    rain_to_string(&ret, val);
    printf("%.*s\n", ret.size, ret.data.s);
  }
}

void rain_ext_print(box *ret, box *val) {
  rain_print(val);
}

void rain_exit(box *ret, box *val) {
  exit(rain_box_to_exit(val));
}

void rain_check_callable(box *val, int num_args) {
  if(BOX_ISNT(val, FUNC)) {
    rain_throw(rain_exc_uncallable);
  }
  else if(val->size != num_args) {
    rain_throw(rain_exc_arg_mismatch);
  }
}

// string helpers

void rain_string_concat(box *ret, box *lhs, box *rhs) {
  if(BOX_ISNT(lhs, STR) && BOX_ISNT(rhs, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }
  else if(BOX_ISNT(rhs, STR)) {
    rain_set_box(ret, lhs);
  }
  else if(BOX_ISNT(lhs, STR)) {
    rain_set_box(ret, rhs);
  }
  else {
    int length = lhs->size + rhs->size;
    char *cat = GC_malloc(length + 1);

    strcat(cat, lhs->data.s);
    strcat(cat + lhs->size, rhs->data.s);

    rain_set_strcpy(ret, cat, length);
  }
}

void rain_to_string(box *ret, box *val) {
  box key;
  box to_str;

  switch(val->type) {
    case ITYP_NULL:
      rain_set_str(ret, "null");
      break;

    case ITYP_INT:
      sprintf(rain_to_str_buf, "%ld", val->data.si);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_FLOAT:
      sprintf(rain_to_str_buf, "%f", val->data.f);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_BOOL:
      rain_set_str(ret, val->data.ui ? "true" : "false");
      break;

    case ITYP_STR:
      rain_set_strcpy(ret, val->data.s, val->size);
      break;

    case ITYP_TABLE:
      rain_set_str(&key, "_str");
      rain_get(&to_str, val, &key);
      if(BOX_IS(&to_str, FUNC) && to_str.size == 1) {
        void (*func_ptr)(box *, box *) = (void (*)(box *, box *))(to_str.data.vp);
        func_ptr(ret, val);
        break;
      }

      sprintf(rain_to_str_buf, "table 0x%08lx", val->data.ui);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_FUNC:
      sprintf(rain_to_str_buf, "func 0x%08lx + %08lx", val->data.ui, (unsigned long)(val->env));
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_CDATA:
      sprintf(rain_to_str_buf, "cdata 0x%08lx", val->data.ui);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;
  }
}

// string AND table helpers

void rain_length(box *ret, box *val) {
  if(BOX_IS(val, STR) || BOX_IS(val, FUNC)) {
    rain_set_int(ret, val->size);
  }
  else if(BOX_IS(val, TABLE)) {
    rain_set_int(ret, rain_array_length(val));
  }
}

void rain_type(box *ret, box *val) {
  rain_set_int(ret, val->type);
}
