#ifndef LSDA_H
#define LSDA_H

#include <stdbool.h>
#include <stdint.h>
#include <unwind.h>

typedef struct _Unwind_Context exception_context_t;
typedef struct _Unwind_Exception exception_t;

bool ponyint_lsda_scan(exception_context_t* context, uintptr_t* lp);

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

#endif
