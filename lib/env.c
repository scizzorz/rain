#include <stdio.h>

#include "rain.h"
#include "env.h"

void rain_init_args(int argc, char **argv) {
  box key;
  box val;
  for(int i = 0; i < argc; ++i) {
    rain_set_int(&key, i);
    rain_set_strcpy(&val, argv[i], strlen(argv[i]));
    rain_put(&rain_args, &key, &val);
  }
}

void rain_get_env(box *ret, box *val) {
  char *env = getenv(val->data.s);
  rain_set_strcpy(ret, env, strlen(env));
}
