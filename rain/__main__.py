import argparse
import os.path
import sys

from . import compiler as C
from . import module as M

parser = argparse.ArgumentParser(description='Compile Rain code.')
parser.add_argument('-r', '--run', action='store_true',
                    help='Execute the compiled code.')
parser.add_argument('-o', '--output', metavar='FILE', default=None,
                    help='Executable file to produce.')
parser.add_argument('-l', '--link', metavar='FILE', action='append',
                    help='Extra files to link with.')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='Quiet the compiler.')

parser.add_argument('--lex', action='store_true',
                    help='Stop and output the results of lexing.')
parser.add_argument('--parse', action='store_true',
                    help='Stop and output the results of parsing.')
parser.add_argument('--emit', action='store_true',
                    help='Stop and output the results of code generation.')

parser.add_argument('file', metavar='FILE', type=str, default='.', nargs='?',
                    help='Main source file.')

args = parser.parse_args()

os.environ['RAINHOME'] = os.path.normpath(os.path.join(sys.argv[0], '../../'))
os.environ['RAINLIB'] = os.path.join(os.environ['RAINHOME'], 'lib')
src = M.find_rain(args.file)
if not src:
  raise Exception('Unable to find module {!r}'.format(args.file))

C.Compiler.quiet = args.quiet
comp = C.get_compiler(src, target=args.output, main=True)

if args.link:
  for tmp in args.link:
    comp.links.add(tmp)

phase = C.phases.building

if args.emit:
  phase = C.phases.emitting

if args.parse:
  phase = C.phases.parsing

if args.lex:
  phase = C.phases.lexing

comp.goodies(phase)

if phase.value > C.phases.emitting.value:
  comp.compile()

if args.run:
  comp.run()
