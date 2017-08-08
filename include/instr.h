#ifndef R_INSTR_H
#define R_INSTR_H

#include "rain.h"

#define NUM_INSTRS 0x17

#define PUSH_CONST 0x00
#define PRINT      0x01
#define UN_OP      0x02
#define BIN_OP     0x03
#define CMP        0x04
#define JUMP       0x05
#define JUMPIF     0x06
#define DUP        0x07
#define POP        0x08
#define SET        0x09
#define GET        0x0A
#define PUSH_TABLE 0x0B
#define PUSH_SCOPE 0x0C
#define NOP        0x0D
#define CALLTO     0x0E
#define RETURN     0x0F
#define IMPORT     0x10
#define CALL       0x11
#define SET_META   0x12
#define GET_META   0x13
#define LOAD       0x14
#define SAVE       0x15
#define FIT        0x16

#define CMP_LT     0x00
#define CMP_LE     0x01
#define CMP_GT     0x02
#define CMP_GE     0x03
#define CMP_EQ     0x04
#define CMP_NE     0x05

#define BIN_ADD    0x00
#define BIN_SUB    0x01
#define BIN_MUL    0x02
#define BIN_DIV    0x03

#define UN_NEG     0x00
#define UN_NOT     0x01

void R_PUSH_CONST(R_vm *vm, R_op *instr);
void R_PRINT(R_vm *vm, R_op *instr);
void R_UN_OP(R_vm *vm, R_op *instr);
void R_BIN_OP(R_vm *vm, R_op *instr);
void R_CMP(R_vm *vm, R_op *instr);
void R_JUMP(R_vm *vm, R_op *instr);
void R_JUMPIF(R_vm *vm, R_op *instr);
void R_DUP(R_vm *vm, R_op *instr);
void R_POP(R_vm *vm, R_op *instr);
void R_SET(R_vm *vm, R_op *instr);
void R_GET(R_vm *vm, R_op *instr);
void R_PUSH_TABLE(R_vm *vm, R_op *instr);
void R_PUSH_SCOPE(R_vm *vm, R_op *instr);
void R_NOP(R_vm *vm, R_op *instr);
void R_CALLTO(R_vm *vm, R_op *instr);
void R_RETURN(R_vm *vm, R_op *instr);
void R_IMPORT(R_vm *vm, R_op *instr);
void R_CALL(R_vm *vm, R_op *instr);
void R_SET_META(R_vm *vm, R_op *instr);
void R_GET_META(R_vm *vm, R_op *instr);
void R_LOAD(R_vm *vm, R_op *instr);
void R_SAVE(R_vm *vm, R_op *instr);
void R_FIT(R_vm *vm, R_op *instr);

void (*R_INSTR_TABLE[NUM_INSTRS])(R_vm *, R_op *);

const char *R_INSTR_NAMES[NUM_INSTRS];

#endif
