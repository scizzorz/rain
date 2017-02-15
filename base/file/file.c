#include "../../core/rain.h"
#include <stdio.h>


// TODO this whole thing is just a temporary proof-of-concept
// it's bad

static char rain_fbuf[4096]; // static buffer

void rain_ext_fopen(box *, box *, box *);
void rain_ext_fwriteline(box *, box *, box *);
void rain_ext_freadline(box *, box *);
void rain_ext_fclose(box *, box *);

void rain_ext_fopen(box *ret, box *fname, box *mode) {
  if(BOX_ISNT(fname, STR) || BOX_ISNT(mode, STR))
    return;

  FILE *fp = fopen(fname->data.s, mode->data.s);
  box key, val;

  rain_set_cdata(ret, (void*)fp);
}

void rain_ext_fwriteline(box *ret, box *this, box *str) {
  if(BOX_ISNT(this, CDATA) || BOX_ISNT(str, STR))
    return;

  FILE *fp = (FILE *)this->data.vp;

  fwrite(str->data.vp, 1, str->size, fp);
  fputc('\n', fp);
}

void rain_ext_freadline(box *ret, box *this) {
  if(BOX_ISNT(this, CDATA))
    return;

  FILE *fp = (FILE *)this->data.vp;

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

void rain_ext_fclose(box *ret, box *this) {
  if(BOX_ISNT(this, CDATA))
    return;

  fclose((FILE *)this->data.vp);
}
