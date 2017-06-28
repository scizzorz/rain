from . import compiler as C
from . import error as Q
from . import module as M
import argparse
import os.path
import sys

parser = argparse.ArgumentParser(description='Compile Rain code.')
parser.add_argument('--output', '-o', metavar='FILE', default=None,
                    help='Executable file to produce.')
parser.add_argument('--lib', '-l', metavar='FILE', action='append',
                    help='Extra libraries to link with.')
parser.add_argument('--quiet', '-q', action='store_true',
                    help='Quiet the compiler.')
parser.add_argument('--verbose', '-v', action='store_true',
                    help='Print extra output.')

parser.add_argument('--lex', '-L', action='store_true',
                    help='Stop and output the results of lexing.')
parser.add_argument('--parse', '-P', action='store_true',
                    help='Stop and output the results of parsing.')
parser.add_argument('--emit', '-S', action='store_true',
                    help='Stop and output the results of code generation.')
parser.add_argument('--run', '-r', action='store_true',
                    help='Execute the compiled code.')
parser.add_argument('--shared', '-s', action='store_true',
                    help='Only compile the main module into a .so file with no links.')

parser.add_argument('file', metavar='RAIN', type=str, default='.', nargs='?',
                    help='Main source file.')
parser.add_argument('links', metavar='LINK', type=str, nargs='*',
                    help='Extra files to link with.')

args = parser.parse_args()


if 'RAINHOME' not in os.environ:
  os.environ['RAINHOME'] = os.path.normpath(os.path.join(sys.argv[0], '../'))

if 'RAINLIB' not in os.environ:
  os.environ['RAINLIB'] = os.path.join(os.environ['RAINHOME'], 'core')

if 'RAINBASE' not in os.environ:
  os.environ['RAINBASE'] = os.path.join(os.environ['RAINHOME'], 'base')

src = M.find_rain(args.file, paths=['.'])
if not src:
  Q.abort("Can't find module {!r}".format(args.file))

C.Compiler.quiet = args.quiet
C.Compiler.verbose = args.verbose
comp = C.get_compiler(src, target=args.output, main=not args.shared)

if args.lib:
  for tmp in args.lib:
    comp.libs.add(tmp)

if args.links:
  for tmp in args.links:
    comp.links.add(tmp)

if args.lex:
  comp.lex()
  comp.write()

elif args.parse:
  comp.parse()
  comp.write()

elif args.emit:
  comp.emit()
  comp.write()

elif args.shared:
  comp.share()

else:
  comp.compile()

if args.run:
  comp.run()
