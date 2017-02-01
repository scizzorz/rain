#ifndef ENV_H
#define ENV_H

extern box *rain_args;

void rain_init_args(int, char**);
void rain_get_env(box *, box *);


#endif
