#ifndef RAIN_H
#define RAIN_H

#include <gc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ITYP_NULL 0
#define ITYP_INT 1
#define ITYP_FLOAT 2
#define ITYP_BOOL 3
#define ITYP_STR 4
#define ITYP_TABLE 5
#define ITYP_FUNC 6
#define ITYP_CDATA 7

#define HASH_SIZE 32

#define BOX_IS(x, t) ((x)->type == ITYP_##t)
#define BOX_ISNT(x, t) ((x)->type != ITYP_##t)

struct column_s;

typedef union {
  unsigned long ui;
  signed long si;
  double f;
  char *s;
  struct column_s **t;
  void *vp;
} cast;

typedef struct {
  unsigned char type;
  cast data;
  int size;
} box;

typedef struct column_s {
  box key;
  box val;
  struct column_s *next;
} column;

int rain_box_to_exit(box *);
void rain_print(box *);
void rain_ext_print(box *, box *);
void rain_exit(box *, box *);
void rain_panic(box *, box *);

void rain_neg(box *, box *);
void rain_not(box *, box *);

void rain_add(box *, box *, box *);
void rain_sub(box *, box *, box *);
void rain_div(box *, box *, box *);
void rain_mul(box *, box *, box *);

unsigned char rain_truthy(box *);
void rain_and(box *, box *, box *);
void rain_or(box *, box *, box *);

void rain_eq(box *, box *, box *);
void rain_ne(box *, box *, box *);
void rain_gt(box *, box *, box *);
void rain_ge(box *, box *, box *);
void rain_lt(box *, box *, box *);
void rain_le(box *, box *, box *);

void rain_string_concat(box *, box *, box*);
void rain_string_length(box *, box *);

box* rain_new_table();
column *rain_new_pair(box *, box *);
unsigned char rain_hash_eq(box *, box *);
unsigned long rain_hash(box *);
column *rain_has(box *, box *);
void rain_get(box *, box *, box *);
void rain_put(box *, box *, box *);

void rain_set_null(box *);
void rain_set_int(box *, signed long);
void rain_set_float(box *, double);
void rain_set_bool(box *, unsigned char);
void rain_set_str(box *, char *);
void rain_set_strcpy(box *, const char *, int);
void rain_set_table(box *);
void rain_set_func(box *, void *);
void rain_set_cdata(box *, void *);

#endif
