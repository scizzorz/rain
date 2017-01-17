#include "util.h"

int rain_table_array_len(box *table) {
  int length = 0;
  box i_box;

  rain_set_int(&i_box, 0);
  while(rain_has(table, &i_box)) {
    ++length;
    rain_set_int(&i_box, length);
  }

  return length;
}

char **rain_table_str_array_gather(box *table, int length) {
  box ret ;
  box i_box;
  char **arr = GC_malloc(sizeof(char*)*length);

  for(int i = 0; i < length; ++i) {
    rain_set_int(&i_box, i);
    rain_get(&ret, table, &i_box);
    arr[i] = ret.data.s;
  }

  return arr;
}
