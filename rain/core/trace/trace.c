#include "rain.h"
#include <stdio.h>

int rain_trace_i = 0;
int rain_trace_depth = 0;

int rain_push(char *module, int line, int column) {
  rain_traces[rain_trace_depth].module = module;
  rain_traces[rain_trace_depth].line = line;
  rain_traces[rain_trace_depth].column = column;
  rain_trace_depth += 1;
  return rain_trace_depth - 1;
}

int rain_pop() {
  rain_trace_depth -= 1;
  return rain_trace_depth;
}

void rain_print_trace(trace_record *trace) {
  if(trace->line == LINE_MAIN) {
    printf("%s: main\n", trace->module);
  }
  else if(trace->line == LINE_INIT) {
    printf("%s: init\n", trace->module);
  }
  else if(trace->line == LINE_UNKNOWN) {
    printf("%s: unknown\n", trace->module);
  }
  else {
    printf("%s: %d:%d\n", trace->module, trace->line, trace->column);
  }
}

void rain_dump() {
  for(rain_trace_i = 0; rain_trace_i < rain_trace_depth; rain_trace_i++) {
    rain_print_trace(rain_traces + rain_trace_i);
  }
}
