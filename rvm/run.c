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

  vm_import(this, argc[1]);
  vm_run(this);

  return 0;
}
