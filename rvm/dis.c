#include "rain.h"
#include <stdio.h>

int main(int argv, char **argc) {
  if(argv < 2) {
    fprintf(stderr, "Usage: %s FILE\n", argc[0]);
    return 1;
  }

  R_vm *this = vm_new();
  if(this == NULL) {
    fprintf(stderr, "Unable to create VM\n");
    return 1;
  }

  if(!vm_import(this, argc[1])) {
    fprintf(stderr, "Unable to import file %s\n", argc[1]);
    return 1;
  }

  printf("Strings (%d):\n", this->num_strings);
  for(uint32_t i=0; i<this->num_strings; i++) {
    printf("  % 2d %s\n", i, this->strings[i]);
  }

  printf("Constants (%d):\n", this->num_consts);
  for(uint32_t i=0; i<this->num_consts; i++) {
    printf("  % 2d ", i);
    R_box_print(this->consts + i);
  }

  printf("Instructions (%d):\n", this->num_instrs);
  for(uint32_t i=0; i<this->num_instrs; i++) {
    printf("  %02x ", i);
    R_op_print(this->instrs + i);
  }

  return 0;
}
