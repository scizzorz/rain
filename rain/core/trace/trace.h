#ifndef TRACE_H
#define TRACE_H

#define LINE_MAIN -1
#define LINE_INIT -2
#define LINE_UNKNOWN -3

typedef struct trace_record {
  char *module;
  int line;
  int column;
} trace_record;

int rain_push(char *, int, int);
int rain_pop();
void rain_print_trace(trace_record *);
void rain_dump();

int rain_trace_i;
int rain_trace_depth;

trace_record rain_traces[1000];

#endif
