from .token import coord
from termcolor import colored as X
import sys
import os.path


def show_line(pos):
  if not pos.file:
    return

  if not os.path.isfile(pos.file):
    return

  with open(pos.file) as tmp:
    for num, line in enumerate(tmp):
      if num+1 == pos.line:
        print(line, end='')
        print(' ' * (pos.col - 1), X('^', 'red', attrs=['bold']), X('~' * (pos.len - 1), 'red', attrs=['bold']), sep='')
        break


def abort(fmt, *args, pos=coord()):
  err = X('error', 'red')

  print('{}: {!s}{}'.format(err, pos, fmt.format(*args)))
  show_line(pos)
  sys.exit(1)

def panic(fmt, *args, pos=coord()):
  raise Exception('{!s}{}'.format(pos, fmt.format(*args)))
