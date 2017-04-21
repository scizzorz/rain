#ifndef BUILTINS_H
#define BUILTINS_H

char rain_to_str_buf[1024];

void rain_print(box *);

void rain_ext_exit(box *, box *);
void rain_ext_meta(box *, box *);
void rain_ext_print(box *, box *);
void rain_ext_panic(box *, box *);
void rain_ext_to_str(box *, box *);
void rain_ext_type(box *, box *);

#endif
