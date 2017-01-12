import argparse
import os
import subprocess
import sys
import tempfile
import traceback

from . import ast as A
from . import emit
from . import lexer as L
from . import module as M
from . import parser as P
from . import types as T
from termcolor import colored as C

parser = argparse.ArgumentParser(description='Compile Rain code.')
parser.add_argument('-r', '--run', action='store_true',
                    help='Execute the compiled code.')
parser.add_argument('-o', '--output', metavar='FILE', default=None,
                    help='Executable file to produce.')
parser.add_argument('-l', '--lib', metavar='FILE', action='append',
                    help='Extra libraries to compile with.')
parser.add_argument('file', metavar='FILE', type=str,
                    help='Main source file.')

args = parser.parse_args()

src = args.file
name = M.Module.find_name(src)

target = args.output or name
libs = args.lib or []
exts = [os.path.join('lib', x) for x in os.listdir('lib') if x.endswith('.c')]

mod = M.Module(name)
with open(src) as tmp:
  text = tmp.read()
stream = L.stream(text)
context = P.context(stream, file=src)
ast = P.program(context)
ast.emit(mod)

handle, tmp_name = tempfile.mkstemp(prefix=name+'.', suffix='.ll')
with os.fdopen(handle, 'w') as tmp:
  tmp.write(mod.ir)

clang = os.getenv('CLANG', 'clang')
subprocess.check_call([clang, '-O2', '-o', target, '-lgc', '-lm', tmp_name] + exts + libs)

if args.run:
  subprocess.check_call([target])
