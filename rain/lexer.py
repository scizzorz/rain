import re
from . import module as M
from .token import bool_token
from .token import dedent_token
from .token import end_token
from .token import float_token
from .token import indent_token
from .token import int_token
from .token import keyword_token
from .token import name_token
from .token import newline_token
from .token import null_token
from .token import operator_token
from .token import string_token
from .token import symbol_token
from .token import table_token
from .token import type_token
from collections import OrderedDict

OPERATORS = (
  '->',
  '<=', '>=', '>', '<', '==', '!=',
  '*', '/', '+', '-',
  '&', '|', '!', '$',
)

KW_OPERATORS = (
)

KEYWORDS = (
  'as', 'break', 'catch', 'continue', 'else', 'export', 'extern', 'for',
  'from', 'func', 'if', 'import', 'in', 'is', 'let', 'loop', 'pass', 'return',
  'save', 'until', 'while', 'with',
)

TYPES = (
  'bool', 'cdata', 'float', 'int', 'str',
)

def factory(data, *, line=None, col=None):
  if data.lower() in KEYWORDS:
    return keyword_token(data.lower(), line=line, col=col)
  elif data.lower() in KW_OPERATORS:
    return operator_token(data.lower(), line=line, col=col)
  elif data.lower() in TYPES:
    return type_token(data.lower(), line=line, col=col)
  else:
    return name_token(M.Module.normalize_name(data), line=line, col=col)

raw = OrderedDict()
raw[r'#.*'] = None
raw[r'""|"(.*?[^\\])"'] = string_token
raw[r'(?:0|[1-9][0-9]*)\.[0-9]+'] = float_token
raw[r'0|[1-9][0-9]*'] = int_token
raw[r'true|false'] = bool_token
raw[r'null'] = null_token
raw[r'table'] = table_token
raw[r'[a-zA-Z_][a-zA-Z0-9_]*'] = factory
raw['|'.join(re.escape(x) for x in OPERATORS)] = operator_token
raw[r'.'] = symbol_token

rules = OrderedDict()
for k, v in raw.items():
  rules[re.compile(k)] = v

indent = re.compile('^[ ]*')

def stream(source):
  indents = [0]
  line = 1
  col = 1

  def skip(amt):
    nonlocal source, col
    source = source[amt:]
    col += amt

  last = None
  while source:
    if source[0] == '\n':
      # skip repeated newlines
      while source and source[0] == '\n':
        skip(1)
        col = 1
        line += 1

      # get this line's indentation
      depth = indent.match(source)
      depth_amt = len(depth.group(0))

      # skip this line if it was just an indentation
      if source and source[depth_amt] == '\n':
        skip(1)
        col = 1
        line += 1
        continue

      # handle indents
      if depth_amt > indents[-1]:
        last = indent_token(line=line, col=col)
        yield last
        indents.append(depth_amt)

      # handle newlines at the same indentation
      else:
        if not isinstance(last, (type(None), indent_token, newline_token)):
          last = newline_token(line=line, col=col)
          yield last

      # handle dedents
      while depth_amt < indents[-1]:
        last = newline_token(line=line, col=col)
        yield dedent_token(line=line, col=col)
        yield last
        del indents[-1]

      skip(depth_amt)
      if not source:
        break

    # skip internal whitespace
    if source[0].isspace():
      skip(1)
      continue

    # tokenize
    for rule, kind in rules.items():
      match = rule.match(source)
      if match:
        value = match.group(0)
        if kind:
          last = kind(value, line=line, col=col)
          yield last
        skip(len(value))
        break

  yield end_token(line=line, col=col)
