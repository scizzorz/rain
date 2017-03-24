#include "rain.h"
#include <pcre.h>
#include <stdio.h>
#include <string.h>


box *rain_exc_pcre_cannot_compile;


/* proof of concept regular expression library */

void table_from_matches(box *table, const char *matched, int *ovector, int pcre_exec_ret) {
  const char *match;
  box key;
  box val;

  rain_set_str(&key, "count");
  rain_set_int(&val, pcre_exec_ret);
  rain_put(table, &key, &val);

  for(int i = 0; i < pcre_exec_ret; ++i) {
    pcre_get_substring(matched, ovector, pcre_exec_ret, i, &match);

    rain_set_int(&key, i);
    rain_set_strcpy(&val, match, strlen(match));
    rain_put(table, &key, &val);

    pcre_free_substring(match);
  }
}


// ret : null | array
// val : cdata
// to_match : str
void rain_ext_pcre_compiled_match(box *ret, box *val, box *to_match) {
  if(BOX_ISNT(val, CDATA) || BOX_ISNT(to_match, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  const char *match;
  int ovector[30]; // TODO should this be dynamic?
  int pcre_exec_ret;

  pcre_exec_ret = pcre_exec((pcre*)val->data.vp, NULL, to_match->data.s, to_match->size, 0, 0, ovector, 30);

  // TODO handle errors better
  if(pcre_exec_ret < 0) {
    return;
    /* probably want this for later, but it's unnecessary right now
    switch(pcre_exec_ret) {
      case PCRE_ERROR_NOMATCH:
        rain_set_null(ret);
        break;
      default:
        rain_set_null(ret);
        break;
    }
    */
  }

  rain_set_table(ret);
  rain_set_env(ret, rain_vt_array);
  table_from_matches(ret, to_match->data.s, ovector, pcre_exec_ret);
}


// ret : cdata
// regex : str
void rain_ext_pcre_compile(box *ret, box *regex) {
  if(BOX_ISNT(regex, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  pcre *compiled;
  const char *pcre_error;
  int pcre_error_offset;

  compiled = pcre_compile(regex->data.s, 0, &pcre_error, &pcre_error_offset, NULL);

  // TODO look at error string, maybe return to user
  if(!compiled) {
    rain_throw(rain_exc_pcre_cannot_compile);
  }

  rain_set_cdata(ret, compiled);
}


// ret : null | array
// regex : str
// to_match : str
// TODO a lot of this is reused from the other two methods, maybe recycle them?
void rain_ext_pcre_match(box *ret, box *regex, box *to_match) {
  if(BOX_ISNT(regex, STR) || BOX_ISNT(to_match, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  pcre *compiled;
  const char *pcre_error;
  const char *match;
  int pcre_error_offset;
  int pcre_exec_ret;
  int ovector[30]; // TODO should this be dynamic?

  compiled = pcre_compile(regex->data.s, 0, &pcre_error, &pcre_error_offset, NULL);

  // TODO look at error string, maybe return to user
  if(!compiled) {
    rain_throw(rain_exc_pcre_cannot_compile);
  }

  pcre_exec_ret = pcre_exec(compiled, NULL, to_match->data.s, to_match->size, 0, 0, ovector, 30);

  // TODO handle errors better
  if(pcre_exec_ret < 0) {
    return;
  }

  rain_set_table(ret);
  rain_set_env(ret, rain_vt_array);
  table_from_matches(ret, to_match->data.s, ovector, pcre_exec_ret);

  pcre_free(compiled);
}
