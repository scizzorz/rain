# Rain

A programming language.

## Nutshells

* Compiled
  * via Python + LLVM
* Dynamically typed
  * Types: `null`, `int`, `float`, `bool`, `string`, `table`, `func`, `cdata`
* Whitespace block delimiters
* Garbage-collected

## Dependencies

Definitely Python 3, LLVM-3.8, and clang-3.8. Check out [requirements.txt](https://github.com/scizzorz/rain/blob/master/requirements.txt) for the Python packages.

## Having fun

Make a fun Rain file:

    let main = func()
      print("Wow, I'm having so much fun right now!")

Use `rainc` on your fun Rain file:

    $ rainc funfile.rn

Then execute the executable:

    $ ./funfile

Check out the [samples](https://github.com/scizzorz/rain/tree/master/samples) for some more fun. All of them should compile and run successfully.
