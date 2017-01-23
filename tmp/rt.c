#include "../lib/rain.h"
#include "lsda.h"
#include <unwind.h>
#include <stdio.h>
#include <stdlib.h>

static exception_t exception;
static uintptr_t landing_pad;

static void exception_cleanup(_Unwind_Reason_Code reason, unwind_exception_t* exception) {
  (void)reason;
  (void)exception;
}

static void set_registers(unwind_exception_t* exception, exception_context_t* context) {
  _Unwind_SetGR(context, __builtin_eh_return_data_regno(0),
      (uintptr_t)exception);
  _Unwind_SetGR(context, __builtin_eh_return_data_regno(1), 0);
  _Unwind_SetIP(context, landing_pad);
}

void rain_throw(box *val) {
  printf("throwing ");
  rain_print(val);

  exception.base.exception_class = 0x5261696E00000000; // "Rain"
  exception.base.exception_cleanup = exception_cleanup;

  rain_set_box(&exception.val, val);

  _Unwind_RaiseException((unwind_exception_t *)&exception);
  abort();
}

void rain_catch(box *ret) {
  rain_set_box(ret, &exception.val);

  printf("catching ");
  rain_print(ret);
}

_Unwind_Reason_Code rain_personality_v0(int version, _Unwind_Action actions,
    uint64_t ex_class, unwind_exception_t* exception,
    exception_context_t* context) {
  (void)ex_class;

  if(version != 1 || exception == NULL || context == NULL)
    return _URC_FATAL_PHASE1_ERROR;

  // The search phase sets up the landing pad.
  if(actions & _UA_SEARCH_PHASE) {
    if(!rain_lsda_scan(context, &landing_pad))
      return _URC_CONTINUE_UNWIND;

    return _URC_HANDLER_FOUND;
  }

  if(actions & _UA_CLEANUP_PHASE) {
    if(!(actions & _UA_HANDLER_FRAME))
      return _URC_CONTINUE_UNWIND;

    // No need to search again, just set the registers.
    set_registers(exception, context);
    return _URC_INSTALL_CONTEXT;
  }

  return _URC_FATAL_PHASE1_ERROR;
}
