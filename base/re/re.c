#include "../../core/rain.h"
#include <pcre.h>
#include <stdio.h>
#include <string.h>


box *rain_exc_pcre_cannot_compile;


/* proof of concept regular expression library */

void table_from_matches(box *table, const char *matched, int *ovector, int pcre_exec_ret) {
  const char *match;
  box key;
  box val;

  rain_set_strcpy(&key, "count", 5);
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

void rain_pcre_compiled_match(box *ret, box *table, box *to_match) {
  if(BOX_ISNT(table, TABLE) || BOX_ISNT(to_match, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  const char *match;
  int ovector[30];
  int pcre_exec_ret;

  box key;
  box val;

  rain_set_strcpy(&key, "_pcre_pointer", 13);
  if(!rain_has(table, &key)) {
    rain_throw(rain_exc_arg_mismatch);
  }
  rain_get(&val, table, &key);

  pcre_exec_ret = pcre_exec((pcre*)val.data.si, NULL, to_match->data.s, to_match->size, 0, 0, ovector, 30);

  /* TODO: handle more errors besides PCRE_ERROR_NOMATCH */
  if(pcre_exec_ret < 0) {
    switch(pcre_exec_ret) {
      case PCRE_ERROR_NOMATCH:
        rain_set_null(ret);
      break;
      default:
	rain_set_null(ret);
      break;
    }
  } else {
    rain_set_table(ret);

    table_from_matches(ret, to_match->data.s, ovector, pcre_exec_ret);
  }
}

void rain_ext_pcre_compile(box *ret, box *regex) {
  if(BOX_ISNT(regex, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  pcre *compiled;
  const char *pcre_error;
  int pcre_error_offset;

  compiled = pcre_compile(regex->data.s, 0, &pcre_error, &pcre_error_offset, NULL);

  /* TODO: look at error string ,maybe return to user */
  if(!compiled) {
    rain_throw(rain_exc_pcre_cannot_compile);
  }

  rain_set_table(ret);

  box key;
  box val;

  /* TODO: how to eventually free the compiled regex? */
  rain_set_strcpy(&key, "_pcre_pointer", 13);
  rain_set_cdata(&val, compiled);
  rain_put(ret, &key, &val);

  rain_set_strcpy(&key, "match", 5);
  rain_set_func(&val, (void*)rain_pcre_compiled_match, 2);
  rain_put(ret, &key, &val);
}

void rain_ext_pcre_match(box *ret, box *regex, box *to_match) {
  if(BOX_ISNT(regex, STR) || BOX_ISNT(to_match, STR)) {
    rain_throw(rain_exc_arg_mismatch);
  }

  pcre *compiled;
  const char *pcre_error;
  const char *match;
  int pcre_error_offset;
  int pcre_exec_ret;
  int ovector[30];

  box key;
  box val;

  compiled = pcre_compile(regex->data.s, 0, &pcre_error, &pcre_error_offset, NULL);

  /* TODO: look at error string, maybe return to user */
  if(!compiled) {
    rain_throw(rain_exc_pcre_cannot_compile);
  }

  pcre_exec_ret = pcre_exec(compiled, NULL, to_match->data.s, to_match->size, 0, 0, ovector, 30);

  /* TODO: handle more errors besides PCRE_ERROR_NOMATCH */
  if(pcre_exec_ret < 0) {
    switch(pcre_exec_ret) {
      case PCRE_ERROR_NOMATCH:
        rain_set_null(ret);
      break;
      default:
	rain_set_null(ret);
      break;
    }
  } else {
    rain_set_table(ret);

    table_from_matches(ret, to_match->data.s, ovector, pcre_exec_ret);
  }

  pcre_free(compiled);
}
