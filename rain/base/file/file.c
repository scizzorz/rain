#include "rain.h"
#include <stdio.h>


// TODO this whole thing is just a temporary proof-of-concept
// it's bad

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
  int bufsize = 4096;
  char *fbuf = GC_malloc(bufsize);

  int i = 0;
  char cur;

  while(1) {
    cur = fgetc(fp);

    if(cur == EOF)
      break;

    if(cur == '\n')
      break;

    if(i >= bufsize) {
      bufsize *= 2;
      fbuf = GC_realloc(fbuf, bufsize);
    }

    fbuf[i] = cur;
    i++;
  }

  if(i == 0 && cur == EOF)
    return;

  fbuf[i] = 0;
  rain_set_str(ret, fbuf);
}

void rain_ext_fread(box *ret, box *this, box *length) {
  if(BOX_ISNT(this, CDATA))
    return;

  if(BOX_ISNT(length, INT))
    return;

  FILE *fp = (FILE *)this->data.vp;
  long size = length->data.si;

  if(size < 0) {
    long restore = ftell(fp);
    fseek(fp, 0L, SEEK_END);
    size = ftell(fp);
    fseek(fp, restore, SEEK_SET);
  }

  char *fbuf = GC_malloc(size + 1);

  long i;
  char cur;

  for(i=0; i<size; i++) {
    cur = fgetc(fp);

    if(cur == EOF)
      break;

    fbuf[i] = cur;
  }

  if(i == 0 && cur == EOF)
    return;

  fbuf[size] = 0;
  rain_set_str(ret, fbuf);
}

void rain_ext_fclose(box *ret, box *this) {
  if(BOX_ISNT(this, CDATA))
    return;

  fclose((FILE *)this->data.vp);
}
