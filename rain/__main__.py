import argparse
import os
import traceback

from . import compiler as C

parser = argparse.ArgumentParser(description='Compile Rain code.')
parser.add_argument('-r', '--run', action='store_true',
                    help='Execute the compiled code.')
parser.add_argument('-o', '--output', metavar='FILE', default=None,
                    help='Executable file to produce.')
parser.add_argument('-l', '--lib', metavar='FILE', action='append',
                    help='Extra libraries to compile with.')
parser.add_argument('-S', '--llvm', metavar='FILE',
                    help='Stop after code generation and write the LLVM IR to this file.')
parser.add_argument('file', metavar='FILE', type=str,
                    help='Main source file.')

args = parser.parse_args()

comp = C.get_compiler(args.file, target=args.output, main=True)
comp.goodies()
comp.compile()

if args.run:
  comp.run()
