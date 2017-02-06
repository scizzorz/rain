from collections import OrderedDict


class Scope:
  def __init__(self):
    self.scopes = []
    self.globals = self.add()

  def add(self):
    scope = OrderedDict()
    self.scopes.append(scope)
    return scope

  def pop(self):
    scope = self.scopes[-1]
    del self.scopes[-1]
    return scope

  @property
  def top(self):
    return self.scopes[-1]

  @property
  def depth(self):
    return len(self.scopes) - 1

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
