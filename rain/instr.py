import ctypes as ct
import struct


class CInstr(ct.Structure):
  _fields_ = [('a', ct.c_uint8),
              ('b', ct.c_uint8),
              ('c', ct.c_uint8),
              ('op', ct.c_uint8)]


class Instr:
  op = 0xFF

  PUSH_CONST = 0x00
  PRINT      = 0x01
  UN_OP      = 0x02
  BIN_OP     = 0x03
  CMP        = 0x04
  JUMP       = 0x05
  JUMPIF     = 0x06
  DUP        = 0x07
  POP        = 0x08
  SET        = 0x09
  GET        = 0x0A
  PUSH_TABLE = 0x0B
  PUSH_SCOPE = 0x0C
  NOP        = 0x0D
  CALLTO     = 0x0E
  RETURN     = 0x0F
  IMPORT     = 0x10
  CALL       = 0x11
  SET_META   = 0x12
  GET_META   = 0x13
  LOAD       = 0x14
  SAVE       = 0x15
  FIT        = 0x16
  JUMPNE     = 0x17
  CATCH_PUSH = 0x18
  CATCH_POP  = 0x19

  def __init__(self):
    pass

  def as_c(self):
    return CInstr(self.op, 0, 0, 0)


class Nx(Instr):
  pass


class Sx(Instr):
  def __init__(self, x):
    self.x = x

  def as_c(self):
    a, b, c, *_ = struct.pack('<i', self.x)
    return CInstr(self.op, a, b, c)


class SBx(Sx):
  def __init__(self, block):
    self.block = block


class Sxyz(Instr):
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z

  def as_c(self):
    a, b, c = map(lambda x: struct.pack('<b', x), (self.x, self.y, self.z))
    return CInstr(self.op, a, b, c)


class Ux(Instr):
  def __init__(self, x):
    self.x = x

  def as_c(self):
    a, b, c, *_ = struct.pack('<I', self.x)
    return CInstr(self.op, a, b, c)


class UBx(Ux):
  def __init__(self, block):
    self.block = block


class Uxyz(Instr):
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z

  def as_c(self):
    a, b, c = map(lambda x: struct.pack('<B', x), (self.x, self.y, self.z))
    return CInstr(self.op, a, b, c)


class PushConst(Ux):
  op = Instr.PUSH_CONST


class Print(Nx):
  op = Instr.PRINT


class Jump(SBx):
  op = Instr.JUMP


class JumpIf(SBx):
  op = Instr.JUMPIF


class JumpNe(SBx):
  op = Instr.JUMPNE


class CatchPush(Nx):
  op = Instr.CATCH_PUSH


class CatchPop(Nx):
  op = Instr.CATCH_POP


class Dup(Ux):
  op = Instr.DUP


class Pop(Nx):
  op = Instr.POP


class Set(Nx):
  op = Instr.SET


class Get(Nx):
  op = Instr.GET


class PushTable(Nx):
  op = Instr.PUSH_TABLE


class PushScope(Nx):
  op = Instr.PUSH_SCOPE


class NOP(Nx):
  op = Instr.NOP


class CallTo(UBx):
  op = Instr.CALLTO


class Return(Nx):
  op = Instr.RETURN


class Import(Nx):
  op = Instr.IMPORT


class Call(Ux):
  op = Instr.CALL


class SetMeta(Nx):
  op = Instr.SET_META


class GetMeta(Nx):
  op = Instr.GET_META


class Load(Nx):
  op = Instr.LOAD


class Save(Nx):
  op = Instr.SAVE


class Fit(Ux):
  op = Instr.FIT


class BinOp(Ux):
  op = Instr.BIN_OP

  ADD    = 0x00
  SUB    = 0x01
  MUL    = 0x02
  DIV    = 0x03


class UnOp(Ux):
  op = Instr.UN_OP

  UN_NEG     = 0x00
  UN_NOT     = 0x01


class CmpOp(Ux):
  op = Instr.CMP

  LT     = 0x00
  LE     = 0x01
  GT     = 0x02
  GE     = 0x03
  EQ     = 0x04
  NE     = 0x05
