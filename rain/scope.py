from . import token as K
from . import ast as A
from collections import OrderedDict

class Namespace(OrderedDict):
  @staticmethod
  def dekey(key):
    if isinstance(key, (A.name_node, A.str_node)):
      key = key.value
    if isinstance(key, (K.name_token, K.string_token)):
      key = key.value
    return key

  def update(self, other):
    other = {self.dekey(key): val for key, val in other.items()}
    super().update(other)

  def __getitem__(self, key):
    return super().__getitem__(self.dekey(key))

  def __setitem__(self, key, val):
    super().__setitem__(self.dekey(key), val)

  def __contains__(self, key):
    return super().__contains__(self.dekey(key))


class Scope:
  def __init__(self):
    self.scopes = []
    self.globals = self.add()

  def add(self):
    scope = Namespace()
    self.scopes.append(scope)
    return scope

  def pop(self):
    scope = self.scopes[-1]
    del self.scopes[-1]
    return scope

  @property
  def top(self):
    return self.scopes[-1]

  def __enter__(self):
    return self.add()

  def __exit__(self, exc_type, exc_val, traceback):
    self.pop()

  def __getitem__(self, key):
    for scope in self.scopes[::-1]:
      if key in scope:
        return scope[key]
    raise KeyError('Key {!r} not found'.format(key))

  def __setitem__(self, key, val):
    self.top[key] = val

  def __contains__(self, key):
    for scope in self.scopes:
      if key in scope:
        return True
    return False
