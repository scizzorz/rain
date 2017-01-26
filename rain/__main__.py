import argparse
import os.path
import sys
import traceback

from . import compiler as C
from . import module as M

parser = argparse.ArgumentParser(description='Compile Rain code.')
parser.add_argument('-r', '--run', action='store_true',
                    help='Execute the compiled code.')
parser.add_argument('-o', '--output', metavar='FILE', default=None,
                    help='Executable file to produce.')
parser.add_argument('-l', '--lib', metavar='FILE', action='append',
                    help='Extra libraries to compile with.')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='Quiet the compiler.')
parser.add_argument('file', metavar='FILE', type=str, default='.', nargs='?',
                    help='Main source file.')

args = parser.parse_args()

os.environ['RAINHOME'] = os.path.normpath(os.path.join(sys.argv[0], '../../'))
os.environ['RAINLIB'] = os.path.join(os.environ['RAINHOME'], 'lib')
src = M.Module.find_file(args.file)
if not src:
  raise Exception('Unable to find module {!r}'.format(args.file))

C.Compiler.quiet = args.quiet
comp = C.get_compiler(src, target=args.output, main=True)
comp.goodies()
comp.compile()

if args.run:
  comp.run()
