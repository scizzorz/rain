#include "rain.h"
#include "except.h"
#include <unwind.h>
#include <stdio.h>
#include <stdlib.h>

static exception_t exception;
static uintptr_t landing_pad;

// LEB encoding

static intptr_t read_sleb128(const uint8_t** data) {
  uintptr_t result = 0;
  uintptr_t shift = 0;
  unsigned char byte;
  const uint8_t* p = *data;

  do {
    byte = *p++;
    result |= (byte & 0x7F) << shift;
    shift += 7;
  } while(byte & 0x80);

  if((byte & 0x40) && (shift < (sizeof(result) << 3)))
    result |= (~(uintptr_t)0) << shift;

  *data = p;
  return result;
}

static uintptr_t read_uleb128(const uint8_t** data) {
  uintptr_t result = 0;
  uintptr_t shift = 0;
  unsigned char byte;
  const uint8_t* p = *data;

  do {
    byte = *p++;
    result |= (byte & 0x7f) << shift;
    shift += 7;
  } while(byte & 0x80);

  *data = p;
  return result;
}

static uintptr_t read_encoded_ptr(const uint8_t** data, uint8_t encoding) {
  const uint8_t* p = *data;

  if(encoding == DW_EH_PE_omit)
    return 0;

  // Base pointer.
  uintptr_t result;

  switch(encoding & 0x0F) {
    case DW_EH_PE_absptr:
      result = *((uintptr_t*)p);
      p += sizeof(uintptr_t);
      break;

    case DW_EH_PE_udata2:
      result = *((uint16_t*)p);
      p += sizeof(uint16_t);
      break;

    case DW_EH_PE_udata4:
      result = *((uint32_t*)p);
      p += sizeof(uint32_t);
      break;

    case DW_EH_PE_udata8:
      result = (uintptr_t)*((uint64_t*)p);
      p += sizeof(uint64_t);
      break;

    case DW_EH_PE_sdata2:
      result = *((int16_t*)p);
      p += sizeof(int16_t);
      break;

    case DW_EH_PE_sdata4:
      result = *((int32_t*)p);
      p += sizeof(int32_t);
      break;

    case DW_EH_PE_sdata8:
      result = (uintptr_t)*((int64_t*)p);
      p += sizeof(int64_t);
      break;

    case DW_EH_PE_sleb128:
      result = read_sleb128(&p);
      break;

    case DW_EH_PE_uleb128:
      result = read_uleb128(&p);
      break;

    default:
      abort();
      break;
  }

  *data = p;
  return result;
}

static uintptr_t read_with_encoding(const uint8_t** data, uintptr_t def) {
  uintptr_t start = (uintptr_t)(*data);
  const uint8_t* p = *data;
  uint8_t encoding = *p++;
  *data = p;

  if(encoding == DW_EH_PE_omit)
    return def;

  uintptr_t result = read_encoded_ptr(data, encoding);

  // Relative offset.
  switch(encoding & 0x70) {
    case DW_EH_PE_absptr:
      break;

    case DW_EH_PE_pcrel:
      result += start;
      break;

    case DW_EH_PE_textrel:
    case DW_EH_PE_datarel:
    case DW_EH_PE_funcrel:
    case DW_EH_PE_aligned:
    default:
      abort();
      break;
  }

  // apply indirection
  if(encoding & DW_EH_PE_indirect)
    result = *((uintptr_t*)result);

  return result;
}

// LSDA management

static bool lsda_init(lsda_t* lsda, exception_context_t* context) {
  const uint8_t* data =
    (const uint8_t*)_Unwind_GetLanguageSpecificData(context);

  if(data == NULL)
    return false;

  lsda->region_start = _Unwind_GetRegionStart(context);
  //-1 because IP points past the faulting instruction
  lsda->ip = _Unwind_GetIP(context) - 1;
  lsda->ip_offset = lsda->ip - lsda->region_start;

  lsda->landing_pads = read_with_encoding(&data, lsda->region_start);
  lsda->type_table_encoding = *data++;

  if(lsda->type_table_encoding != DW_EH_PE_omit) {
    lsda->type_table = (const uint8_t*)read_uleb128(&data);
    lsda->type_table += (uintptr_t)data;
  }
  else {
    lsda->type_table = NULL;
  }

  lsda->call_site_encoding = *data++;

  uintptr_t length = read_uleb128(&data);
  lsda->call_site_table = data;
  lsda->action_table = data + length;

  return true;
}

static bool lsda_scan(exception_context_t* context, uintptr_t* lp) {
  lsda_t lsda;

  if(!lsda_init(&lsda, context))
    return false;

  const uint8_t* p = lsda.call_site_table;

  while(p < lsda.action_table) {
    uintptr_t start = read_encoded_ptr(&p, lsda.call_site_encoding);
    uintptr_t length = read_encoded_ptr(&p, lsda.call_site_encoding);
    uintptr_t landing_pad = read_encoded_ptr(&p, lsda.call_site_encoding);

    // Pony ignores the action index, since it uses only cleanup landing pads.
    read_uleb128(&p);

    if((start <= lsda.ip_offset) && (lsda.ip_offset < (start + length))) {
      // No landing pad.
      if(landing_pad == 0)
        return false;

      // Pony doesn't read the type index or look up types. We treat cleanup
      // landing pads the same as any other landing pad.
      *lp = lsda.landing_pads + landing_pad;
      return true;
    }
  }

  return false;
}

// Exception helpers

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

// Rain API

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
    if(!lsda_scan(context, &landing_pad))
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
