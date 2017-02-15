#ifndef TABLE_H
#define TABLE_H

#include "../core.h"

box* rain_new_table();
column *rain_new_pair(box *, box *);
unsigned char rain_hash_eq(box *, box *);
unsigned long rain_hash(box *);
column *rain_has(box *, box *);
box *rain_get_ptr(box *, box *);
void rain_get(box *, box *, box *);
void rain_put(box *, box *, box *);

#endif