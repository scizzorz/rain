#ifndef EXCEPT_H
#define EXCEPT_H

/*
DISCLAIMER: Much of this code was borrowed and modified from the Pony language.
Please see the PONY-LICENSE in the repository root, or view it at
https://github.com/ponylang/ponyc
*/

#include "rain.h"
#include <stdbool.h>
#include <stdint.h>
#include <unwind.h>

typedef struct _Unwind_Context exception_context_t;
typedef struct _Unwind_Exception unwind_exception_t;

typedef struct exception_t {
  unwind_exception_t base;
  box val;
} exception_t;

typedef struct lsda_t {
  uintptr_t region_start;
  uintptr_t ip;
  uintptr_t ip_offset;
  uintptr_t landing_pads;

  const uint8_t* type_table;
  const uint8_t* call_site_table;
  const uint8_t* action_table;

  uint8_t type_table_encoding;
  uint8_t call_site_encoding;
} lsda_t;

enum {
  DW_EH_PE_absptr = 0x00,
  DW_EH_PE_uleb128 = 0x01,
  DW_EH_PE_udata2 = 0x02,
  DW_EH_PE_udata4 = 0x03,
  DW_EH_PE_udata8 = 0x04,
  DW_EH_PE_sleb128 = 0x09,
  DW_EH_PE_sdata2 = 0x0A,
  DW_EH_PE_sdata4 = 0x0B,
  DW_EH_PE_sdata8 = 0x0C,
  DW_EH_PE_pcrel = 0x10,
  DW_EH_PE_textrel = 0x20,
  DW_EH_PE_datarel = 0x30,
  DW_EH_PE_funcrel = 0x40,
  DW_EH_PE_aligned = 0x50,
  DW_EH_PE_indirect = 0x80,
  DW_EH_PE_omit = 0xFF
};

void rain_throw(box *);
void rain_ext_throw(box *, box *);
void rain_abort();
void rain_catch(box *);
_Unwind_Reason_Code rain_personality_v0(int, _Unwind_Action, uint64_t, unwind_exception_t *, exception_context_t *);

// from the standard lib

box *rain_exc_error;
box *rain_exc_arg_mismatch;
box *rain_exc_uncallable;
box *rain_exc_interrupt;
box *rain_exc_fpe;
box *rain_exc_segfault;

#endif
