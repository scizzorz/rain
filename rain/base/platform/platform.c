#include "rain.h"

#ifdef __linux__
#define LINUX_BOOL 1
#define MAC_BOOL 0
#define PLATFORM_STR "linux"

#elif __APPLE__
#define LINUX_BOOL 0
#define MAC_BOOL 1
#define PLATFORM_STR "mac"

#else
#define LINUX_BOOL 0
#define MAC_BOOL 0
#define PLATFORM_STR "unknown"

#endif

void rain_ext_get_platform(box *ret) {
  rain_set_str(ret, PLATFORM_STR);
}

void rain_ext_is_linux(box *ret) {
  rain_set_bool(ret, LINUX_BOOL);
}

void rain_ext_is_mac(box *ret) {
  rain_set_bool(ret, MAC_BOOL);
}
