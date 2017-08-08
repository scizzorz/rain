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

  uint32_t i = 0;

  do {
    printf("% 3d --------\n", i++);
    vm_dump(this);
    getchar();
  } while(vm_step(this));

  return 0;
}
