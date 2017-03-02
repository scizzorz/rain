---
layout: default
title: Rain - a programming language
---

# Rain

A dynamically-typed, whitespace-delimited, garbage-collected language focused
on simplicity, expressiveness, and extensibility via a powerful C API.

<div id="toc-sidebar" markdown="block">

* This text is scraped
{:toc}

</div>

## Language Reference

### Lexical Analysis

* **Operators**
  * `->` - lambda expression operator
  * `::` - metatable assignment operator
  * `<=`, `>=`, `<`, `>`, `==`, `!=` - comparison operators
  * `+`, `-`, `*`, `/` - arithmetic operators (`-` is also a unary negation)
  * `&`, `|` - logical boolean operators
  * `!` - logical not operator
  * `$` - string concatenation operator
* **Reserved keywords**
  * `as`, `break`, `catch`, `continue`, `else`, `export`, `for`, `foreign`,
    `func`, `if`, `import`, `in`, `let`, `library`, `link`, `loop`, `macro`,
    `pass`, `return`, `save`, `until`, `while`, `with`,
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
  * Inside of `[]`, `{}`, and `()` pairs, indentation is ignored.

### Types

Rain supports 8 data types:

* `int` - 64-bit signed integers
* `float` - 64-bit precision floats
* `str` - character pointers with an associated length. String literals are
  null-terminated for compatibility with C
* `bool` - `true` or `false`
* `func` - a function
* `null` - the single value `null` (it *is* possible for C extensions to create
  other `null`-typed values, but it's not recommended!)
* `table` - the only complex data type - a hash table
* `cdata` - indicates that this value is only manipulated by C extensions.
  Usually used to store pointers

### Values

All values are copied "by value". A called function's parameter is a copy of
the caller's argument. However, because the "value" of a `table` object is a 
pointer to its hash table, mutating a table will mutate the referenced hash table.

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

The `return` keyword exits the function and returns its expression. An empty 
or missing `return` statement will terminate the function and return `null`. 

A secondary shorthand definition exists for single expressions:

    let add = func(x, y) -> x + y

#### The `save` statement

The `save` statement acts as a "lazy" `return` - it saves a value to return,
but does not immediately terminate the function. After saving a value, empty 
or missing `return` statements *will* return the saved value. Explicit `return` 
statements will override any saved values.

    let add = func(x, y)
      save x + y
      print("This will still be printed.")

    let add2 = func(x, y)
      save "Incorrect sum"
      print("This will still be printed.")
      return x + y # this will override the previously saved value

#### Calling

Functions can be called by wrapping a list of arguments in parentheses.

    let sum = add(3, 4)

#### Closures

Creating a function in a local scope (ie, inside another function) enables it
to close over all non-global variables in the outer scope(s). Variables being
closed over are *copied by value* into a *closure environment* for the function.

    let i = 0
    let counter = func()
      save i
      i = i + 1

    print(counter()) # 0
    print(counter()) # 1 - internal variable is changed
    print(i)         # 0 - original variable is untouched

The closure environment of a function can be inspected and mutated from outside
of the function via indexing.

TODO update example

    print(counter.i) # 2 - inspect closure environment from outside
    counter.i = 0    # mutate closure environment from outside
    print(counter()) # 0 - external mutations are visible internally

#### The `main` function

Every Rain program must define a no-argument `main` function at the top level:

    let main = func()
      print("Hello!")

This function serves as the entry point of the program.
The return value of `main` is used as the program's exit status:
* integers exit as their value (floats are converted to integers)
* `false` exits as `1`
* All other values exit as `0`

### `pass` statement

`pass` is simply a no-op instruction:

    let main = func()
      pass # does nothing

### The `if` statement

    let test = func(n)
      if n == 0
        print("n is zero")
      else if n > 0
        print("n is positive")
      else
        print("n is negative")

All values except `null`, `false`, `0`, and `0.0` are "truthy" - that is, they 
evaluate to true in boolean contexts like `if` statements. Null `cdata` values 
will also evaluate to false.

### Loops

Rain supports four types of loops: `loop`, `while`, `until`, and `for`, as well
as `break` and `continue` statements to control iteration. In addition, Rain 
supports conditional variants - `break if` and `continue if` - which evaluate the 
following expression and only terminate the loop or continue to the next iteration 
if their expression is truthy.

#### `loop`

An infinite loop that can only be terminated via the `break` statement:

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

    for n in range(20)
      print(n)

An *iterator* is a no-argument function that returns the next value in a 
sequence.

    let range = func(n)
      let i = 0
      let iter = func() # this is the "iterator" - a no-arg function
        if i == n
          return null   # terminate iteration
        save i          # the next value in the sequence
        i = i + 1

      return iter

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

    let a = true | print("Condition was falsy.")   # shorts - does not print
    let b = false & print("Condition was truthy.") # shorts - does not print

    let x = null | "default"  # x = "default"

#### Comparison

The comparison operators (`<=`, `>=`, `<`, `>`) can operate on floats and
integers, coercing integers to floats when necessary. Strings are compared in
lexicographic order.

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

Rain supports a prototypal model via *metatables*. When looking up a key in a
table, a missing key will return `null`. However, if the table contains a
metatable, lookup proceed to that table instead. The "metatable chain" will be
followed until the key is found or a metatable is missing. A metatable can be
added using the `::` operator.

    let mt = table
    mt.name = "meta"

    let x = table :: mt
    print(x.name) # "meta" - x.name isn't found, but x.mt.name is
    print(x.age) # null - x.age isn't found, neither is x.mt.age

Assignment to an index *does not* traverse the metatable chain:

    x.name = "x"
    print(x.name) # "x"
    print(mt.name) # "meta"

An object's metatable can be retrieved using the `meta(val)` builtin:

    print(meta(x) == mt) # true

#### OOP

Classes and inheritance can be emulated via metatables and methods:

    let rectangle = table
    rectangle.init = func(self, w, h)
      self.w = w
      self.h = h
    rectangle.area = func(self)
      return self.w * self.h

    let square = table :: rectangle
    square.init = func(self, size)
      self.w = size
      self.h = size

    let r = table :: rectangle
    let s = table :: square

    r:init(3, 4)    # "init" is defined on rectangle
    print(r:area()) # 12 - "area" is defined on rectangle

    s:init(5)       # "init" is defined on square
    print(s:area()) # 25 - "area" is first defined on rectangle

#### Arrays

Rain has no formal "arrays" - it simply mimics them by using tables with keys
from `0` to `n`:

    let arr = table
    arr[0] = "Zero"
    arr[1] = "One"
    arr[2] = "Two"

A shorthand syntax is available for defining arrays:

    let arr = ["Zero", "One", "Two"]

#### Dictionaries

A shorthand syntax is also available for defining dictionaries:

    let rain = {name = "Rain", type = "Language"}

By default, the key of a dictionary item is interpreted the same as
`.` notation would be - that includes name normalization. To use non-names as
the keys, use `[]`:

    let rain = {[0] = "Zero", ["__not_normalized__"] = true}

### Panics

Throw exceptions with the builtin `panic(val)`. Standard exceptions are found
in the builtin `except` module.

    panic(except.arg_mismatch)

By default, a panicking program will unwind the stack until it reaches main,
which will catch the panic and print a message.

You can throw any value.

    panic(3)
    panic("Hello")

#### Catch calls

Using a `?` in a function call will allow it to stop a panic and return the
recovered value instead.

    let div = func(x, y)
      if y == 0
        panic("Division by zero")
      return x/y

    let a = div(10, 2) # returns 5
    let b = div?(10, 0) # div will panic, but its value will be recovered
                        # and returned: "Division by zero"
    let c = div(10, 0) # panics and unwinds the entire stack

#### Catch blocks

Using a `catch` block, you can catch any exception that occurs inside the block
and store it in a variable. The return value of a panicking function as well
as any code after the panic is undefined.

    catch err
      let a = div(10, 2)
      let b = div?(10, 0)
      let c = div(10, 0)
      let d = div(15, 3)

    print(a)   # 3
    print(b)   # "Division by zero"
    print(c)   # undefined - could be anything
    print(d)   # undefined - could be anything
    print(err) # "Division by zero"

### Contexts

The `with` statement allows you to pass anonymous function blocks to
a *context* function.

    let ctx = func(block) # the context function - receives an anonymous func
      print("Initialization")
      block() # use the anonymous func
      print("Clean up")

    with ctx
      print("Anonymous block")

The `with..as` statement allows the anonymous block to accept arguments from
the context function.

    let ctx2 = func(block)
      print("Initialization")
      block("Port", "Starboard")
      print("Clean up")

    with ctx2 as left, right
      print("The left side is: " $ left)
      print("The right side is: " $ right)

### Modules

Code can be put in separate files, called "modules", and then reused inside
other modules.

#### `export` statement

In order for a variable to be visible to other modules, it must be declared
with the `export` statement instead of the `let` statement:

    export name = "math"
    export pi = 3.1415926535

`export` statements can only be used in the global scope.

#### `import` statement

Other modules can be used with the `import` statement:

    import math

    let main = func()
      print(math.name) # "math"
      print(math.pi)   # 3.1415926535

Imported modules are just tables that are populated with the exported values of
a module.

The module can be renamed using the `import..as` statement:

    import math as m

Relative paths can also be used:

    import "../math"

When importing module `XYZ`, several paths are searched for a file matching
`XYZ.rn`, `XYZ`, and `XYZ/_pkg.rn`. The first file found is used for the
module. The default paths searched are the current module's base directory, the
current working directory and any paths found in `$RAINPATH`. `$RAINBASE` and
`$RAINLIB` are also searched.

Imported modules are never exported unless explicitly exported:

    import math as math_private
    export math = math_private

`import` statements can only be used in the global scope.

#### `init` Function

Before any `main()` function is called, if any imported modules have an
`init()` function, it will be called. `init` functions are called in the order
of import - that is, when compiling a program, the order modules are listed as
being built by the compiler.

#### Packages

Several modules can be combined together into a *package* by placing them in
the same directory and adding a file called `_pkg.rn` to the directory. The
`_pkg.rn` can be imported with the directory name, while other modules will
need to be imported as a path.

#### Module names

Typically, a module's name is simply the normalized version with the `.rn` suffix removed:

    my_file.rn -> myfile

To avoid name conflicts with other modules, package modules are prefixed
with the package name.

    base/_pkg.rn       -> base
    base/array.rn      -> base.array
    base/test/_pkg.rn  -> base.test
    base/test/extra.rn -> base.test.extra

#### Modules as metatables

Because modules are simply tables, they can be used as metatables / classes.

    import array

    let arr = table :: array
    arr[0] = "Zero"
    arr[1] = "One"
    arr[2] = "Two"

    for val in arr:values() # values is a method defined in base.array
      print(val)

In fact, if `array` is imported, then array literals automatically have it set
as their metatable:

    import array

    let arr = ["Zero", "One", "Two"]

    for val in arr:values()
      print(val)

The same is true of dictionary literals and the `dict` module.

### Macros

### Standard library

Things that come with Rain. Usually.

#### Built-ins

* Guaranteed to be in scope in every module.
* Found in the `core/_pkg.rn` file.

* `print(val)` - print a value to stdout
* `exit(val)` - abort the program
* `panic(val)` - raise an exception and unwind the stack
* `type(val)` - return an integer corresponding to a value's type
* `to_str(val)` - return a string representation of a value
* `env` - the `core.env` module
* `except` - the `core.except` module

#### `core` package

Things Rain needs to function correctly.

##### `core.env`

The execution environment.

* `args` - command line arguments passed to the program
* `get(name)` - return an environment variable

##### `core.except`

Standard exceptions.

* `error` - the base metatable for all exceptions
* `arg_mismatch` - raised when a function is called with incorrect
  arguments
* `uncallable` - raised when a value that is not a function is called

##### `core.ast`

Used in macros.

##### `core.types`

Contains type helpers.

##### `core.ops`

Contains the functions used by Rain's operators.

#### `base` package

Things that Rain likes to have.

##### `base.array`

A module containing array helpers. Often used as a metatable. If imported,
array literals have it preset as their metatable.

##### `base.dict`

A module containing dict helpers. Often used as a metatable. If imported,
dictionary literals have it preset as their metatable.

#### `base.macros`

Some helper macros.

### C extensions

One of the primary goals of Rain is to be easily extendable with C.

#### C API

#### `link` statement

Instructs the Rain compiler to link with a file. The search paths are the same
as the `import` statement.

    link "myfile.c"

#### `library` statement

Instructs the Rain compiler to link with a shared library. The search paths are
defined by your system configuration.

    library "m"    # link with libm
    library "pcre" # link with libpcre

#### `foreign` functions

Return a function reference to an external C function. The parameter names are
currently ignored, but the number of them is significant. The function name
can be a name or a string literal.

    # get a reference to `void rain_add(box *ret, box *lhs, box *rhs)`
    let add = foreign "rain_add"(lhs, rhs)

#### `export..as foreign` statement

Sometimes a global value needs to be shared between Rain and the C API.

    // core/except/except.h
    box *rain_exc_arg_mismatch;

And:

    # core/except/_pkg.rn
    export arg_mismatch = table :: error
    export arg_mismatch as foreign "rain_exc_arg_mismatch"

The exported name can be a name or a string literal.
