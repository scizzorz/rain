from . import types as T
from . import error as Q

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
      if items[key_hash % max].constant is None:
        break

      if items[key_hash % max].key == key_node:
        break

      key_hash += 1

    return key_hash % max


  # Insert a box into a static table
  def put(self, table_box, key_node, val):
    key = self.module.emit(key_node)

    lpt_ptr = table_box.lpt_ptr

    if getattr(lpt_ptr, 'arr_ptr', None) is None:
      Q.abort('Global value is opaque')

    arr_ptr = lpt_ptr.arr_ptr
    item = T.item([T.i32(1), key, val])
    item.key = key_node

    cur = lpt_ptr.initializer.constant[0].constant
    max = lpt_ptr.initializer.constant[1].constant
    items = arr_ptr.initializer.constant

    idx = self.idx(table_box, key_node)
    if items[idx].constant is None:
      cur += 1

    # TODO resize if cur > max / 2! currently, it infinite loops.

    items[idx] = item
    arr_ptr.initializer = arr_ptr.value_type(items)
    arr_gep = arr_ptr.gep([T.i32(0), T.i32(0)])

    lpt_ptr.initializer = lpt_ptr.value_type([T.i32(cur), T.i32(max), arr_gep])
    lpt_ptr.arr_ptr = arr_ptr


  # Return a box from a static table
  def get(self, table_box, key_node):
    lpt_ptr = table_box.lpt_ptr
    arr_ptr = lpt_ptr.arr_ptr
    items = arr_ptr.initializer.constant

    idx = self.idx(table_box, key_node)
    if items[idx].constant is None:
      return T.null

    return items[idx].constant[2]


  # Allocate a static table
  def alloc(self, name):
    arr_typ = T.arr(T.item, T.HASH_SIZE)
    arr_ptr = self.module.add_global(arr_typ, name=name + '.array')
    arr_ptr.initializer = arr_typ([None] * T.HASH_SIZE)
    arr_gep = arr_ptr.gep([T.i32(0), T.i32(0)])

    lpt_typ = T.lpt
    lpt_ptr = self.module.add_global(lpt_typ, name=name)
    lpt_ptr.initializer = lpt_typ([T.i32(0), T.i32(T.HASH_SIZE), arr_gep])
    lpt_ptr.arr_ptr = arr_ptr

    return self.from_ptr(lpt_ptr)


  # Return a box from a static table
  def from_ptr(self, ptr):
    box = T._table(ptr)
    box.lpt_ptr = ptr  # save this for later!
    return box


  # Return a pointer to a static table's value box
  def get_box_ptr(self, table_box, key_node):
    idx = self.idx(table_box, key_node)
    return table_box.lpt_ptr.arr_ptr.gep([T.i32(0), T.i32(idx), T.i32(2)])


  # Repair a static table box from another one
  def repair(self, new_box, old_box):
    if getattr(old_box, 'lpt_ptr', None):
      new_box.lpt_ptr = old_box.lpt_ptr
