from .token import coord
from termcolor import colored as X
import os.path
import sys


def show_line(pos, hi=lambda x: X(x, 'red', attrs=['bold'])):
  if not pos.file:
    return

  if not os.path.isfile(pos.file):
    return

  with open(pos.file) as tmp:
    for num, line in enumerate(tmp):
      if num + 1 == pos.line:
        print(line, end='')
        print(' ' * (pos.col - 1), hi('^'), hi('~' * (pos.len - 1)), sep='')
        break


def abort(fmt, *args, pos=coord()):
  err = X('error', 'red')

  print('{}: {!s}{}'.format(err, pos, fmt.format(*args)))
  show_line(pos)
  sys.exit(1)


def warn(fmt, *args, pos=coord()):
  err = X('warning', 'blue')

  print('{}: {!s}{}'.format(err, pos, fmt.format(*args)))
  show_line(pos, hi=lambda x: X(x, 'blue', attrs=['bold']))


def hint(fmt, *args, pos=coord()):
  err = X('hint', 'green')

  print('{}: {!s}{}'.format(err, pos, fmt.format(*args)))
  show_line(pos, hi=lambda x: X(x, 'green', attrs=['bold']))


def panic(fmt, *args, pos=coord()):
  raise Exception('{!s}{}'.format(pos, fmt.format(*args)))
