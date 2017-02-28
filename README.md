# Rain

A dynamically-typed, whitespace-delimited, garbage-collected language focused
on simplicity, expressiveness, and extensibility via a powerful C API.

Check out the [docs](https://scizzorz.github.io/rain/) for more.

## Dependencies

Definitely Python 3, LLVM-3.9, clang-3.9, [`libunwind`](http://www.nongnu.org/libunwind/), and [`libgc`](https://www.hboehm.info/gc/). Check out [requirements.txt](https://github.com/scizzorz/rain/blob/master/requirements.txt) for the Python packages.

The regular expression package (`base.re`) module requires `libpcre`.

## Having fun

Make a fun Rain file:

    let main = func()
      print("Wow, I'm having so much fun right now!")

Use `rainc` on your fun Rain file:

    $ rainc funfile.rn

Then execute the executable:

    $ ./funfile

Check out the [samples](https://github.com/scizzorz/rain/tree/master/samples) for some more fun. All of them should compile and run successfully.
