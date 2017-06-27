#ifndef CORE_H
#define CORE_H

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

struct box_s;
struct table_s;

typedef union {
  unsigned long ui;
  signed long si;
  double f;
  char *s;
  struct table_s *lpt;
  void *vp;
} cast;

typedef struct box_s {
  unsigned char type;
  int size;
  cast data;
  struct box_s *env;
} box;

typedef struct item_s {
  box key;
  box val;
} item;

typedef struct table_s {
  int cur;
  int max;
  item **items;
} table;

int rain_box_to_exit(box *);
void rain_check_callable(box *, int);
int rain_has_meta(box *);
box *rain_box_malloc();

#endif
