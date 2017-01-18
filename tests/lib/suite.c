#include <criterion/criterion.h>

#include "../../lib/rain.h"

Test(array, length) {
  box arr;
  box i_box;
  rain_set_table(&arr);
  rain_set_int(&i_box, 0);
  cr_assert_eq(0, rain_array_length(&arr));
}
