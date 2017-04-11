from . import types as T
import functools


externs = {
  'main': T.func(T.i32, (T.i32, (T.ptr(T.ptr(T.i8))))),
  'GC_malloc': T.func(T.ptr(T.i8), [T.i32]),

  'rain_abort': T.vfunc(),
  'rain_box_malloc': T.func(T.arg, []),
  'rain_box_to_exit': T.func(T.i32, [T.arg]),
  'rain_catch': T.vfunc(T.arg),
  'rain_check_callable': T.vfunc(T.arg, T.i32),
  'rain_init_args': T.vfunc(T.i32, T.ptr(T.ptr(T.i8))),
  'rain_init_gc': T.func(T.i32, []),
  'rain_personality_v0': T.func(T.i32, [], var_arg=True),
  'rain_throw': T.vfunc(T.arg),

  'rain_push': T.func(T.i32, [T.ptr(T.i8), T.i32, T.i32]),
  'rain_pop': T.func(T.i32, []),
  'rain_dump': T.func(T.void, []),

  'rain_neg': T.vfunc(T.arg, T.arg),
  'rain_lnot': T.vfunc(T.arg, T.arg),

  'rain_add': T.bin,
  'rain_sub': T.bin,
  'rain_mul': T.bin,
  'rain_div': T.bin,

  'rain_and': T.bin,
  'rain_or': T.bin,

  'rain_eq': T.bin,
  'rain_ne': T.bin,
  'rain_gt': T.bin,
  'rain_ge': T.bin,
  'rain_lt': T.bin,
  'rain_le': T.bin,

  'rain_string_concat': T.bin,

  'rain_new_table': T.func(T.arg, []),
  'rain_get_ptr': T.func(T.arg, [T.arg, T.arg]),
  'rain_put': T.bin,
  'rain_get': T.bin,
}


class Runtime:
  def __init__(self, module):
    self.module = module

  def declare(self):
    for name, typ in externs.items():
      self.module.add_func(typ, name=name)

  def _getfunc(self, name):
    return self.module.get_global(name)

  @property
  def main(self):
    func = self._getfunc('main')
    func.attributes.personality = self.personality
    return func

  @property
  def personality(self):
    return self._getfunc('rain_personality_v0')

  def __getattr__(self, key):
    key = 'rain_' + key
    if key in externs:
      return functools.partial(self.module.call, self._getfunc(key))

  def __getitem__(self, key):
    key = 'rain_' + key
    if key in externs:
      return self._getfunc(key)
