#include "rand.h"
#include <stdlib.h>

void rain_ext_rand(box * ret) {
  double num_rand = (double)rand()  / (double)RAND_MAX;
  rain_set_float(ret, num_rand);
}

void rain_ext_srand(box * ret, box * seed) {
  srand(seed->data.ui);
}
