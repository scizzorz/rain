#include "rain.h"

void rain_ext_get_platform(box *ret) {
  #ifdef __linux__
    rain_set_str(ret, "linux");
  #elif __APPLE__
    rain_set_str(ret, "mac");
  #else
    rain_set_str(ret, "unknown");
  #endif
}
