from . import error as Q
from . import types as T
from llvmlite import ir


class Static:
  def __init__(self, module):
    self.module = module

  # Return the index to insert / fetch from a static table
  # Note: if the key isn't found, the returned index points to a None constant
  def idx(self, table_box, key_node):
    lpt_ptr = table_box.lpt_ptr
    arr_ptr = lpt_ptr.arr_ptr

    max = lpt_ptr.initializer.constant[1].constant
    items = arr_ptr.initializer.constant
    key_hash = key_node.hash()

    while True:
      if not isinstance(items[key_hash % max], ir.GlobalVariable):
        break

      if items[key_hash % max].initializer.key == key_node:
        break

      key_hash += 1

    return key_hash % max

  # Insert a box into a static table
  def put(self, table_box, key_node, val, pair=None):
    lpt_ptr = table_box.lpt_ptr
    cur = lpt_ptr.initializer.constant[0].constant
    max = lpt_ptr.initializer.constant[1].constant

    if getattr(lpt_ptr, 'arr_ptr', None) is None:
      Q.abort('Global value is opaque')

    # resize the table
    if cur + 1 >= max / 2:
      # save old pointers
      # TODO how do we delete them from the module?
      old_arr_ptr = lpt_ptr.arr_ptr
      old_items = old_arr_ptr.initializer.constant

      # make new pointers
      name = self.module.uniq(old_arr_ptr.name[:-6])
      new_arr_ptr = self.alloc_arr(name, max * 2)
      new_arr_gep = new_arr_ptr.gep([T.i32(0), T.i32(0)])

      # reassign them
      lpt_ptr.arr_ptr = new_arr_ptr
      lpt_ptr.initializer = T.lpt([T.i32(0), T.i32(max * 2), new_arr_gep])

      # reinsert everything
      for i, pair in enumerate(old_items):
        if isinstance(pair, ir.GlobalVariable):
          self.put(table_box, pair.initializer.key, None, pair=pair)

      # update cur/max
      cur = lpt_ptr.initializer.constant[0].constant
      max = lpt_ptr.initializer.constant[1].constant

    key = self.module.emit(key_node)

    arr_ptr = lpt_ptr.arr_ptr
    items = arr_ptr.initializer.constant

    idx = self.idx(table_box, key_node)

    # we're adding a new pair here
    if not isinstance(items[idx], ir.GlobalVariable):
      cur += 1
      items[idx] = pair or self.module.add_global(T.item)

    # don't need to do this if we're recycling a pair
    if not pair:
      items[idx].initializer = T.item([key, val])
      items[idx].initializer.key = key_node

    arr_ptr.initializer = arr_ptr.value_type(items)
    arr_gep = arr_ptr.gep([T.i32(0), T.i32(0)])

    lpt_ptr.initializer = lpt_ptr.value_type([T.i32(cur), T.i32(max), arr_gep])
    lpt_ptr.arr_ptr = arr_ptr

    ret = items[idx].gep([T.i32(0), T.i32(1)])
    return ret

  # Return a box from a static table
  def get(self, table_box, key_node):
    lpt_ptr = table_box.lpt_ptr
    arr_ptr = lpt_ptr.arr_ptr
    items = arr_ptr.initializer.constant

    idx = self.idx(table_box, key_node)
    if not isinstance(items[idx], ir.GlobalVariable):
      return T.null

    return items[idx].initializer.constant[1]

  # Allocate a static table
  def alloc(self, name, size=T.HASH_SIZE):
    arr_ptr = self.alloc_arr(name, size)
    arr_gep = arr_ptr.gep([T.i32(0), T.i32(0)])

    lpt_typ = T.lpt
    lpt_ptr = self.module.add_global(lpt_typ, name=name)
    lpt_ptr.initializer = lpt_typ([T.i32(0), T.i32(size), arr_gep])
    lpt_ptr.arr_ptr = arr_ptr

    return lpt_ptr

  # Allocate the inner item array for a table
  def alloc_arr(self, name, size=T.HASH_SIZE):
    arr_typ = T.arr(T.ptr(T.item), size)
    arr_ptr = self.module.add_global(arr_typ, name=name + '.array')
    arr_ptr.initializer = arr_typ([None] * size)

    return arr_ptr

  # Allocate a static table and put it in a box
  def new_table(self, name, size=T.HASH_SIZE):
    return self.from_ptr(self.alloc(name, size))

  # Return a box from a static table
  def from_ptr(self, ptr):
    box = T._table(ptr)
    box.lpt_ptr = ptr  # save this for later!
    return box

  # Repair a static table box from another one
  def repair(self, new_box, old_box):
    if getattr(old_box, 'lpt_ptr', None):
      new_box.lpt_ptr = old_box.lpt_ptr
