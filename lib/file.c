#include "rain.h"

#include <stdio.h>

// TODO this whole thing is just a temporary proof-of-concept
// it's bad

static char rain_fbuf[4096]; // static buffer

void rain_fopen(box *, box *, box *);
void rain_fwriteline(box *, box *, box *);
void rain_freadline(box *, box *);
void rain_fclose(box *, box *);

void rain_fopen(box *ret, box *fname, box *mode) {
  if(BOX_ISNT(fname, STR) || BOX_ISNT(mode, STR))
    return;

  FILE *fp = fopen(fname->data.s, mode->data.s);
  box key, val;

  rain_set_table(ret);

  rain_set_str(&key, "_file");
  rain_set_data(&val, (void*)fp);
  rain_put(ret, &key, &val);

  rain_set_str(&key, "readline");
  rain_set_func(&val, (void*)rain_freadline);
  rain_put(ret, &key, &val);

  rain_set_str(&key, "writeline");
  rain_set_func(&val, (void*)rain_fwriteline);
  rain_put(ret, &key, &val);

  rain_set_str(&key, "close");
  rain_set_func(&val, (void*)rain_fclose);
  rain_put(ret, &key, &val);
}

void rain_fwriteline(box *ret, box *this, box *str) {
  if(BOX_ISNT(this, TABLE) || BOX_ISNT(str, STR))
    return;

  box key, file;
  rain_set_str(&key, "_file");
  rain_get(&file, this, &key);

  FILE *fp = (FILE *)file.data.vp;

  fwrite(str->data.vp, 1, str->size, fp);
  fputc('\n', fp);
}

void rain_freadline(box *ret, box *this) {
  if(BOX_ISNT(this, TABLE))
    return;

  box key, file;
  rain_set_str(&key, "_file");
  rain_get(&file, this, &key);

  FILE *fp = (FILE *)file.data.vp;

  int i = 0;
  char cur;

  while(1) {
    cur = fgetc(fp);

    if(cur == EOF)
      break;

    if(cur == '\n')
      break;

    rain_fbuf[i] = cur; // what's a buffer overflow?
    i++;
  }

  if(i == 0 && cur == EOF)
    return;

  rain_fbuf[i] = 0;
  rain_set_strcpy(ret, rain_fbuf, i);
}

void rain_fclose(box *ret, box *this) {
  if(BOX_ISNT(this, TABLE))
    return;

  box key, file;
  rain_set_str(&key, "_file");
  rain_get(&file, this, &key);

  fclose((FILE *)file.data.vp);
}
