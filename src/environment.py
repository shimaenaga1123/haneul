import os

from rpython.rlib import rfile
from rpython.rlib import rrandom, rtimer
from rpython.rlib.rarithmetic import intmask, r_uint

from bytecode_parser import BytecodeParser
from constant import *
from error import InvalidType

LINE_BUFFER_LENGTH = 1024


def print_char_builtin_func(args):
  ch = args[0]
  assert ch is not None
  if isinstance(ch, ConstChar):
    os.write(1, ch.charval.encode('utf-8'))
    return ConstNone()
  else:
    raise InvalidType(u"문자", ch.type_name())

def stringize_builtin_func(args):
  l = []
  for ch in args[0].show():
    l.append(ConstChar(ch))

  return list_to_struct(l)

def input_builtin_func():
  stdin, stdout, stderr = rfile.create_stdio()
  line = stdin.readline(LINE_BUFFER_LENGTH)
  parser = BytecodeParser(line)

  result = []
  while parser.code[parser.pos] != '\n':
    result.append(parser.parse_char())

  return list_to_struct(result)

def to_integer_builtin_func(args):
  a = args[0]
  if isinstance(a, ConstStruct):
    s = collect_string(a)
    try:
      return ConstInteger(int(s.encode('utf-8')))
    except:
      return ConstNone()
  elif isinstance(a, ConstChar):
    try:
      return ConstInteger(int(a.charval.encode('utf-8')))
    except:
      return ConstNone()
  elif isinstance(a, ConstReal):
    return ConstInteger(int(a.doubleval))
  elif isinstance(a, ConstInteger):
    return a
  else:
    raise InvalidType(u"정수화할 수 있는", a.type_name())

def to_real_builtin_func(args):
  a = args[0]
  if isinstance(a, ConstStruct):
    s = collect_string(a)
    try:
      return ConstReal(float(s.encode('utf-8')))
    except:
      return ConstNone()
  elif isinstance(a, ConstChar):
    try:
      return ConstReal(float(a.charval.encode('utf-8')))
    except:
      return ConstNone()
  elif isinstance(a, ConstReal):
    return a
  elif isinstance(a, ConstInteger):
    return ConstReal(float(a.intval))
  else:
    raise InvalidType(u"실수화할 수 있는", a.type_name())

def random_builtin_func():
  rng = rrandom.Random(seed=r_uint(rtimer.read_timestamp()))
  return ConstInteger(intmask(rng.genrand32()))

def get_unicode_func(args):
  a = args[0]
  if isinstance(a, ConstChar):
    return ConstInteger(ord(a.charval[0]))
  else:
    raise InvalidType(u"문자", a.type_name())

def nth_unicode_func(args):
  a = args[0]
  if isinstance(a, ConstInteger):
    return ConstChar(chr(a.intval))
  else:
    raise InvalidType(u"정수", a.type_name())


print_char_builtin = ConstFunc([(u"을", None)], None, print_char_builtin_func)
stringize_builtin = ConstFunc([(u"을", None)], None, stringize_builtin_func)
input_builtin = ConstFunc([], None, input_builtin_func)
to_integer_builtin = ConstFunc([(u"을", None)], None, to_integer_builtin_func)
to_real_builtin = ConstFunc([(u"을", None)], None, to_real_builtin_func)
random_builtin = ConstFunc([], None, random_builtin_func)
get_unicode_builtin = ConstFunc([(u"의", None)], None, get_unicode_func)
nth_unicode_builtin = ConstFunc([(u"번째", None)], None, nth_unicode_func)

default_globals = {
    u"문자로 보여주다": print_char_builtin,
    u"문자열로 바꾸다": stringize_builtin,
    u"정수로 바꾸다": to_integer_builtin,
    u"실수로 바꾸다": to_real_builtin,
    u"난수를 가져오다": random_builtin,
    u"입력받다": input_builtin,
    u"유니코드 값": get_unicode_builtin,
    u"유니코드 문자": nth_unicode_builtin,
}

