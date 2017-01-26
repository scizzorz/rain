#ifndef STRING_H
#define STRING_H

#define FMT_SIZE 1024
char fmt_buf[FMT_SIZE];

void rain_to_string(box *, box *);
void rain_fmt(box *, box *, box *);

void rain_string_to_int(box *, box *);

#endif
