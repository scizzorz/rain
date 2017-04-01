#ifndef ARITH_H
#define ARITH_H

#include "../core.h"

void rain_binary_magic(box *, box *, box *, char *);

void rain_neg(box *, box *);
void rain_not(box *, box *);

void rain_add(box *, box *, box *);
void rain_sub(box *, box *, box *);
void rain_div(box *, box *, box *);
void rain_mul(box *, box *, box *);

unsigned char rain_truthy(box *);
void rain_ext_truthy(box *, box *);
void rain_and(box *, box *, box *);
void rain_or(box *, box *, box *);

void rain_eq(box *, box *, box *);
void rain_ne(box *, box *, box *);
void rain_gt(box *, box *, box *);
void rain_ge(box *, box *, box *);
void rain_lt(box *, box *, box *);
void rain_le(box *, box *, box *);

void rain_string_concat(box *, box *, box*);

#endif
