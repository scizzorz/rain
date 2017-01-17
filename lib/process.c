#include "rain.h"
#include "util.h"

#include <sys/wait.h>
#include <stdlib.h>
#include <unistd.h>

#define BUF_SIZE 4096

void rain_process_output(box *, box *);



void rain_process_output(box *ret, box *command) {
  if(BOX_ISNT(command, TABLE)) {
    return;
  }

  /* create the cmd array to pass to exec */

  int cmd_len = rain_table_array_len(command);

  if (cmd_len == 0) {
    return;
  }

  char **strs = rain_table_str_array_gather(command, cmd_len);

  char **cmd = GC_malloc(sizeof(char*)*cmd_len+1);
  for(int i = 0; i < cmd_len; ++i) {
    cmd[i] = strs[i];
  }
  cmd[cmd_len] = (char*)0;

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

  if(pid == 0) {
    /* child */
    dup2(link[1], STDOUT_FILENO);
    close(link[0]);
    close(link[1]);

    execvp(cmd[0], cmd);

    return;
  } else {
    /* parent */
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
