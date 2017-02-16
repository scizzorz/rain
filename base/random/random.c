#include "random.h"
#include <stdlib.h>

void rain_ext_rand(box * ret) {
  rain_set_int(ret, rand());
}

void rain_ext_srand(box * ret, box * seed) {
  srand(seed->data.ui);
}
