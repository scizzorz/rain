#include "rain.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void rain_print(box *val) {
  if(BOX_IS(val, STR)) {
    printf("%.*s\n", val->size, val->data.s);
  }
  else {
    box ret;
    rain_set_null(&ret);
    rain_ext_to_str(&ret, val);
    printf("%.*s\n", ret.size, ret.data.s);
  }
}

void rain_ext_exit(box *ret, box *val) {
  exit(rain_box_to_exit(val));
}

void rain_ext_meta(box *ret, box *val) {
  if(rain_has_meta(val)) {
    rain_set_box(ret, val->env);
  }
}

void rain_ext_print(box *ret, box *val) {
  rain_print(val);
}

void rain_ext_panic(box *ret, box *val) {
  rain_panic(val);
}

void rain_ext_to_str(box *ret, box *val) {
  box str_key;
  box str_func;

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
      // look up ["str"] on metatable
      if(rain_has_meta(val)) {
        rain_set_str(&str_key, "str");
        rain_set_null(&str_func);
        rain_get(&str_func, val->env, &str_key);

        if(BOX_IS(&str_func, FUNC) && str_func.size == 1) {
          void (*func_ptr)(box *, box *) = (void (*)(box *, box *))(str_func.data.vp);
          if(rain_has_meta(&str_func)) {
            rain_set_box(ret, str_func.env);
          }
          func_ptr(ret, val);
          break;
        }
      }

      sprintf(rain_to_str_buf, "table 0x%08lx", val->data.ui);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_FUNC:
      sprintf(rain_to_str_buf, "func 0x%08lx", val->data.ui);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;

    case ITYP_CDATA:
      sprintf(rain_to_str_buf, "cdata 0x%08lx", val->data.ui);
      rain_set_strcpy(ret, rain_to_str_buf, strlen(rain_to_str_buf));
      break;
  }
}

void rain_ext_type(box *ret, box *val) {
  rain_set_int(ret, val->type);
}
