---
layout: default
title: Rain - a programming language
---

# Rain

A dynamically-typed, whitespace-delimited, garbage-collected language focused
on simplicity, expressiveness, and extensibility via a powerful C API.

## Quirks

* Names are normalized by removing all underscores and converting all letters
  to lower case.

## Language Reference

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
* `table` - the only compound data type - a hash table
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
By default, all functions return `null` - a blank `return` statement will
simply terminate the function and return `null`.

A secondary shorthand definition is available for functions that only do small
calculations that fit in one expression:

    let add = func(x, y) -> x + y

#### `save` statement

#### Calling

#### Closures

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

#### Boolean

#### Comparison

### Tables

#### Indexing

#### Methods

#### "Objects" / "classes"

### Exceptions

#### Catch calls

#### Catch blocks

### Contexts

### Modules

#### `import` statement

#### `export` statement

#### Packages

### Standard library

### C extensions

#### C API

#### `link` statement

#### `foreign` functions

#### `export..as foreign` statement
