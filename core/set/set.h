#ifndef SET_H
#define SET_H

#include "../core.h"

void rain_set_box(box *, box *);
void rain_set_null(box *);
void rain_set_int(box *, signed long);
void rain_set_float(box *, double);
void rain_set_bool(box *, unsigned char);
void rain_set_str(box *, char *);
void rain_set_strcpy(box *, const char *, int);
void rain_set_table(box *);
void rain_set_func(box *, void *, int);
void rain_set_cdata(box *, void *);

#endif
