---
layout: default
title: Rain - a programming language
---

# Rain

A dynamically-typed, whitespace-delimited, garbage-collected language focused
on simplicity, expressiveness, and extensibility via a powerful C API.

## Language Reference

### Lexical Analysis

* **Operators**
  * `->` - used only for "lambda" functions
  * `<=`, `>=`, `<`, `>`, `==`, `!=` - comparison operators
  * `+`, `-`, `*`, `/` - arithmetic operators (`-` is also a unary negation)
  * `&`, `|` - logical boolean operators
  * `!` - logical not operator
  * `$` - string concatenation operator
* **Reserved keywords**
  * `as`, `break`, `catch`, `continue`, `else`, `export`, `for`, `foreign`,
    `from`, `func`, `if`, `import`, `in`, `let`, `library`, `link`, `loop`,
    `macro`, `pass`, `return`, `save`, `until`, `while`, `with`,
* **String Literals** - `"" | "(.*?[^\\])"`
* **Float Literals** - `(0 | [1-9][0-9]*) \. [0-9]+`
* **Integer Literals** - `0 | [1-9][0-9]*`
* **Boolean Literals** - `true`, `false`
* **Table Literals** - `table`
* **Names** - `[a-zA-Z_][a-zA-Z0-9_]*`
  * Names are normalized by removing all underscores and converting all letters
    to lower case.
* **Comments** - line comments are indicated by a `#`
* **Indentation** - Spaces only; tabs are invalid.
  * Two spaces is advised, but any increase in indentation is valid. Dedents
    must return to a previous indentation level.

### Types

Rain supports 8 data types:

* `int` - 64-bit signed integers
* `float` - 64-bit precision floats
* `str` - pointers unsigned 8-bit integers with an associated size. Usually
  null-terminated for compatibility with C, but not required
* `bool` - either of the keywords `true` or `false`
* `func` - a function
* `null` - the single value `null` (it *is* possible for C extensions to create
  other `null`-typed values, but it's not recommended!)
* `table` - the only complex data type - a hash table
* `cdata` - indicates that this value is only manipulated by C extensions.
  Usually used to store pointers

### Values

All values are copied "by value" - meaning functions cannot mutate their
arguments nor can they mutate values in outer scopes that they close over.
However, because the "value" of a `table` object is a pointer to its hash
table, mutating a table will mutate its value outside of the function.

### Assignment

You can introduce new variables using the `let` keyword:

    let x = "Hello, world!"

All values are strongly typed (eg, adding a table and an integer will raise an
exception), but the variables are not typed:

    let x = "Hello, world!"
    x = 5

Note that `let` is only used to *introduce a new variable* - once the variable
has been introduced, `let` is no longer required.

### Functions

Functions are defined using the `func` keyword and a list of parameters:

    let add = func(x, y)
      return x + y

The `return` keyword behaves exactly like most other programming languages.
By default, all functions return `null` - an empty `return` statement will
simply terminate the function and return `null`.

A secondary shorthand definition is available for functions that only do small
calculations that fit in one expression:

    let add = func(x, y) -> x + y

#### `save` statement

The `save` statement acts as a "lazy" `return` - it saves a value to return,
but does not immediately terminate the function. When the function returns, the
most recently saved value will be used as its return value. After saving a
value, subsequent empty `return` statements *will* return the saved value.
Explicit `return` statements will override any saved values.

#### Calling

Function values can be called by wrapping a list of arguments in parentheses.

#### Closures

Creating a function in a local scope (ie, inside another function) enables it
to close over any non-global variables in the outer scope(s). Values being
closed over are *copied* into a *closure environment* for the function. If the
function mutates those variables, they are persistent *inside* the function but
will not mutate the original variable.

The closure environment of a function can be inspected and mutated from outside
of the function by via indexing. External mutations are visible inside the
function and internal mutations are visible outside the function.

#### `main` function

Every Rain program must define a no-argument `main` function at the top level:

    let main = func()
      print("Hello!")

This function serves as the program entry point - similar to `main` in C/C++.
The return value of `main` is used as the program's exit status - `null` and
`true` evaluate to exit status `0`, while `int` and `float` types evaluate to
their value. All other values evaluate to `0`.

### Comments

Rain supports line comments with the `#` symbol.

    # This is a comment.
    let x = 5 # This value is used later.

### `pass` statement

`pass` is simply a no-op instruction:

    let main = func()
      pass # does nothing

### `if` statement

`if` behaves like most other programming languages:

    let test = func(n)
      if n == 0
        print("n is zero")
      else if n > 0
        print("n is positive")
      else
        print("n is negative")

All values except `null`, `false`, the integer `0`, and `0.0` are "truthy" -
that is, they evaluate to true in boolean contexts like `if` statements. Null
`cdata` values will also evaluate to false.

### Loops

Rain supports four types of loops: `loop`, `while`, `until`, and `for`, as well
as the typical `break` and `continue` statements to control iteration. In
addition, Rain supports conditional variants - `break if` and `continue if` -
which evaluate the following expression and only terminate the loop or continue
to the next iteration if their expression is truthy.

#### `loop`

An infinite loop that can only be terminated via `break` statements:

    let n = 0
    loop
      n = n + 1
      print(n)
      break if n == 20

#### `while`

A loop that repeats *while* a condition is met:

    let n = 0
    while n < 20
      n = n + 1
      print(n)

#### `until`

A loop that repeats *until* a condition is met:

    let n = 0
    until n == 20
      n = n + 1
      print(n)

#### `for`

A loop that repeatedly calls an *iterator* and binds its return value to a
variable. The loop is terminated when the iterator returns `null`.

    for n in iter.range(20)
      print(n)

An *iterator* is simply a no-argument function that simply returns the next
value in a sequence.

### Operators

#### Arithmetic

The operators (`+`, `-`, `*`, `/`) can only operate on floats and integers.
Mixed operand types will produce a float, while two integer operands produces
an integer, *including* integer divison (ie, `5/2 == 2`)

#### Boolean

The boolean operators (`&`, `|`) evaluate their operands based on their
"truthiness" value. They will short-circuit if the second operand is not
necessary (ie, `&` short-circuits if the first argument is falsy, while `|`
short-circuits if the first argument is truthy). If an operator short-circuits,
its first operand is returned. If an operator does not short-circuit, its
second operand is evaluated and returned.

#### Comparison

The comparison operators (`<=`, `>=`, `<`, `>`) can operate on floats and
integers, coercing integers to floats when necessary. String comparisons are
also possible, comparing in lexicographic order.

The equality operators (`==`, `!=`) strictly compare for hashing equality (ie,
if two values will index into the same location in a table). This includes type
checking as well as value checking. A consequence of this is that the
expressions `x <= y` and `x >= y` are not equivalent to the expressions
`x < y | x == y` and `x > y | x == y`, respectively. Function, table, and
cdata values are compared by their *value*, not their contents - if two tables
contain the same values but are not the same table reference, they are not
equal.

*Note: this behavior may be changed in the future.*

### Tables

Tables are the only complex data structure available in Rain. They are
implemented as unordered hash tables.

    let x = table

#### Indexing

Tables can be indexed using square brackets:

    x["name"] = "Rain"
    x[0] = "Zero"

Any value can be used as a key into the table. Because strings are very
frequently used as indices, you can use standard `.` notation:

    x.name = "Rain" # equivalent to x["name"] = "Rain"

When using a value from a table, missing keys will return `null`.

*Note: when using `.` notation, the name normalization rules apply! `x._name` is equivalent to `x["name"]`, not `x["_name"]`!*

#### Methods

Function values can be added to tables just like any other value. However,
because functions stored in a table frequently want to operate on the table
that contains them, there is an additional notation that can be used to
implicitly pass a reference to the contained function:

    let x = table
    x.name = "Rain"
    x.hello = func(self)
      print(self.name)

    x.print(x) # . requires an explicit pass of x to itself
    x:print()  # : adds an implicit pass of x to itself

By convention, the first parameter is named `self`, but this is not required.

#### Metatables

Rain supports a prototypal model via the `metatable` key. When looking up a key
in a table, a missing key will return `null`. However, if the table contains
another table assigned to the `metatable` key, the lookup will proceed to that
table instead. This "metatable chain" will be followed until the key is found
or a metatable is missing.

    let meta = table
    meta.name = "meta"
    let x = table
    print(x.name) # null
    x.metatable = meta
    print(x.name) # "meta" - x.name isn't found, but x.metatable.name is

Assignment to an index *does not* traverse the metatable chain:

    x.name = "x"
    print(x.name) # "x"
    print(meta.name) # "meta"

Because metatable use is pervasive, syntactic sugar is available for assigning
a metatable to a new table object:

    let y = table from meta
    print(y.name) # "meta"

#### "Objects" / "classes"

Classes and inheritance can be emulated via metatables and methods:

    let rectangle = table
    rectangle.init = func(self, w, h)
      self.w = w
      self.h = h
    rectangle.area = func(self)
      return self.w * self.h

    let square = table from rectangle
    square.init = func(self, size)
      self.w = size
      self.h = size

    let r = table from rectangle
    let s = table from square

    r:init(3, 4)    # "init" is defined on rectangle
    print(r:area()) # 12 - "area" is defined on rectangle

    s:init(5)       # "init" is defined on square
    print(s:area()) # 25 - "area" is first defined on rectangle

### Exceptions

#### Catch calls

#### Catch blocks

### Contexts

### Modules

#### `import` statement

#### `export` statement

#### Packages

#### `init` Function

### Macros

### Standard library

#### Built-ins

#### `core` package

#### `base` package

### C extensions

#### C API

#### `link` statement

#### `library` statement

#### `foreign` functions

#### `export..as foreign` statement
