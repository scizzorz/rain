#include "util.h"

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
