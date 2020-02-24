# -*- coding: utf-8 -*-
from rpython.rlib.jit import JitDriver, promote, elidable

from instruction import *
from constant import *
from error import HaneulError, InvalidType, ArgNumberMismatch, UnboundVariable, UnboundJosa


jitdriver = JitDriver(greens=['pc', 'frame'],
                      reds=['stack', 'call_stack', 'global_vars', 'global_var_names'])


class CallFrame:
  # _immutable_fields_ = [
  #     'code[*]', 'free_vars[*]', 'slot_start']

  def __init__(self, table, insts, free_list, slot_index):
    self.pc = 0
    self.const_table = table
    self.code = insts
    self.free_vars = free_list
    self.slot_start = slot_index

  @elidable
  def get_constant(self, index):
    return self.const_table[index]


# class Program:
#   def __init__(self, global_var_names, global_vars, frame):
#     self.global_var_names = global_var_names
#     self.global_vars = global_vars + [None] *\
#         (len(global_var_names) - len(global_vars))

#     self.stack = []
#     self.call_stack = [frame]

#   def push(self, v):
#     self.stack.append(v)

#   def pop(self):
#     return self.stack.pop()

#   def peek(self, n=0):
#     return self.stack[len(self.stack) - n - 1]

#   def current_frame(self):
#     return self.call_stack[-1]


def run(global_var_names, global_vars, frame):
  global_var_names = promote(global_var_names)
  global_vars = global_vars + [None] *\
      (len(global_var_names) - len(global_vars))

  stack = []
  call_stack = [frame]

  while True:
    frame = call_stack[-1]

    if frame.pc >= len(frame.code):
      if len(call_stack) == 1:
        break

      result = stack.pop()
      while len(stack) != frame.slot_start:
        stack.pop()

      stack.append(result)

      call_stack.pop()
      continue

    jitdriver.jit_merge_point(
        pc=frame.pc, global_vars=global_vars, global_var_names=global_var_names, frame=frame,
        stack=stack, call_stack=call_stack)

    inst = frame.code[frame.pc]
    inst = promote(inst)
    try:
      if inst.opcode == INST_PUSH:
        # print "PUSH"
        stack.append(frame.get_constant(inst.operand_int))

      elif inst.opcode == INST_POP:
        # print "POP"
        stack.pop()

      elif inst.opcode == INST_LOAD:
        # print "LOAD"
        stack.append(stack[frame.slot_start + inst.operand_int])

      elif inst.opcode == INST_LOAD_DEREF:
        stack.append(frame.free_vars[inst.operand_int])

      elif inst.opcode == INST_LOAD_GLOBAL:
        result = global_vars[inst.operand_int]
        if result is None:
          raise UnboundVariable(u"변수 '%s'를 찾을 수 없습니다." %
                                global_var_names[inst.operand_int])
        else:
          stack.append(result)

      elif inst.opcode == INST_STORE_GLOBAL:
        global_vars[inst.operand_int] = stack.pop()

      elif inst.opcode == INST_CALL:
        # print "CALL"
        given_arity = len(inst.operand_str)

        value = stack.pop()
        if value.type == TYPE_FUNC:
          for (i, josa) in enumerate(inst.operand_str):
            if josa == u"_":
              for (k, v) in value.josa_map.iteritems():
                if v is None:
                  value.josa_map[k] = stack.pop()
                  break
            else:
              if josa in value.josa_map:
                value.josa_map[josa] = stack.pop()
              else:
                raise UnboundJosa(u"조사 '%s'를 찾을 수 없습니다." % josa)
                return

          args = value.josa_map.values()
          rest_arity = 0
          for v in args:
            if v is None:
              rest_arity += 1

          if rest_arity > 0:
            stack.append(value)
          else:  # rest_arity == 0
            if value.builtinval is None:
              func_object = value.funcval
              func_frame = CallFrame(func_object.const_table, func_object.code,
                                     func_object.free_vars, len(stack))
              stack.extend(args)
              call_stack.append(func_frame)

              jitdriver.can_enter_jit(
                  pc=frame.pc, global_vars=global_vars, global_var_names=global_var_names, frame=frame,
                  stack=stack, call_stack=call_stack)
            else:
              func_result = value.builtinval(args)
              stack.append(func_result)

        else:
          raise InvalidType(
              u"%s 타입의 값은 호출 가능하지 않습니다." % get_type_name(value.type))

        #   raise argnumbermismatch(
        #       u"이 함수 %d개의 인수를 받지만 %d개의 인수가 주어졌습니다." % (func_object.arity, inst.operand_int))

      elif inst.opcode == INST_JMP:
        # print "JMP"
        frame.pc = inst.operand_int
        continue

      elif inst.opcode == INST_POP_JMP_IF_FALSE:
        # print "POPJMPIFFALSE"
        value = stack.pop()
        if value.type != TYPE_BOOLEAN:
          raise InvalidType(u"여기에는 참 또는 거짓 타입을 필요로 합니다.")

        if value.boolval == False:
          frame.pc = inst.operand_int
          continue

      elif inst.opcode == INST_FREE_VAR_LOCAL:
        value = stack[frame.slot_start + inst.operand_int]
        stack[-1].funcval.free_vars.append(value)

      elif inst.opcode == INST_FREE_VAR_FREE:
        value = frame.free_vars[inst.operand_int]
        stack[-1].funcval.free_vars.append(value)

      elif inst.opcode == INST_NEGATE:
        # print "NEGATE"
        value = stack.pop()
        stack.append(value.negate())
      else:
        rhs, lhs = stack.pop(), stack.pop()
        if inst.opcode == INST_ADD:
          # print "ADD"
          stack.append(lhs.add(rhs))
        elif inst.opcode == INST_SUBTRACT:
          # print "SUBTRACT"
          stack.append(lhs.subtract(rhs))
        elif inst.opcode == INST_MULTIPLY:
          # print "MULTIPLY"
          stack.append(lhs.multiply(rhs))
        elif inst.opcode == INST_DIVIDE:
          # print "DIVIDE"
          stack.append(lhs.divide(rhs))
        elif inst.opcode == INST_MOD:
          # print "MOD"
          stack.append(lhs.mod(rhs))
        elif inst.opcode == INST_EQUAL:
          # print "EQUAL"
          stack.append(lhs.equal(rhs))
        elif inst.opcode == INST_LESS_THAN:
          # print "LESS_THAN"
          stack.append(lhs.less_than(rhs))
        elif inst.opcode == INST_GREATER_THAN:
          # print "GREATER_THAN"
          stack.append(lhs.greater_than(rhs))

      frame.pc += 1
    except HaneulError as e:
      if e.error_line == 0:
        e.error_line = inst.line_number
      raise e

  """
    # print "[",
    for c in self.stack:
      if c.type == TYPE_INTEGER:
        # print c.intval,
      if c.type == TYPE_REAL:
        # print c.doubleval,
      if c.type == TYPE_STRING:
        # print c.stringval,
      if c.type == TYPE_BOOLEAN:
        # print c.boolval,
      if c.type == TYPE_FUNC:
        # print c.funcval,
        # print ", ",
        # print "]"
    """
