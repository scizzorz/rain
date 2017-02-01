#ifndef ENV_H
#define ENV_H

#include "../rain.h"

box *rain_args;

void rain_init_args(int, char**);
void rain_get_env(box *, box *);


#endif
