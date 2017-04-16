#include "rain.h"
#include <gc.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>


#define BUF_SIZE 4096


void rain_ext_process_output(box *ret, box *command) {
  if(BOX_ISNT(command, TABLE)) {
    return;
  }

  box key;
  box val;

  // find out how many parameters we have
  int len = 0;
  while(1) {
    rain_set_null(&val);
    rain_set_int(&key, len);
    rain_get(&val, command, &key);
    if(BOX_ISNT(&val, STR)) {
      break;
    }
    len++;
  }

  // pack the parameters into a char**
  char **cmd = GC_malloc(sizeof(char*) * len);

  for(int i=0; i<len; i++) {
    rain_set_int(&key, i);
    rain_get(&val, command, &key);
    cmd[i] = val.data.s;
  }

  cmd[len] = (char*)0;

  /* fork a child to execute the command and read the output in the parent */
  /* only stdout is read */

  int link[2];
  pid_t pid;

  int str_size = BUF_SIZE;
  char *str = GC_malloc(str_size);
  int str_len = 0;

  if(pipe(link) == -1) {
    return;
  }

  pid = fork();

  if(pid == -1) {
    return;
  }

  // child
  if(pid == 0) {
    dup2(link[1], STDOUT_FILENO);
    close(link[0]);
    close(link[1]);

    execvp(cmd[0], cmd);

    return;
  }

  // parent
  else {
    close(link[1]);

    int n = 0;
    char buf[BUF_SIZE];
    while(0 != (n = read(link[0], buf, sizeof(buf)))) {
      if(str_len + n >= str_size) {
        char *old_str = str;
        str_size += BUF_SIZE;
        str = GC_malloc(str_size);
        strncpy(str, old_str, str_len);
      }
      strncpy(str+str_len, buf, n);
      str_len += n;
    }

    wait(0);
  }

  rain_set_strcpy(ret, str, str_len);
}
