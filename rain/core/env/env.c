#include "rain.h"
#include <stdlib.h>
#include <string.h>


void rain_init_args(int argc, char **argv) {
  box key;
  box val;
  rain_set_env(rain_args, rain_vt_array);

  for(int i = 0; i < argc; ++i) {
    rain_set_int(&key, i);
    rain_set_strcpy(&val, argv[i], strlen(argv[i]));
    rain_put(rain_args, &key, &val);
  }
}

void rain_ext_get_env(box *ret, box *val) {
  char *env = getenv(val->data.s);
  if(env) {
    rain_set_strcpy(ret, env, strlen(env));
  }
}
