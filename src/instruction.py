INST_PUSH = 0
INST_POP = 1
INST_LOAD_LOCAL = 2
INST_STORE_LOCAL = 3
INST_LOAD_DEREF = 4
INST_STORE_GLOBAL = 5
INST_LOAD_GLOBAL = 6
INST_CALL = 7
INST_ADD_STRUCT = 8
INST_MAKE_STRUCT = 9
INST_GET_FIELD = 10
INST_JMP = 11
INST_POP_JMP_IF_FALSE = 12
INST_FREE_VAR = 13
INST_ADD = 14
INST_SUBTRACT = 15
INST_MULTIPLY = 16
INST_DIVIDE = 17
INST_MOD = 18
INST_EQUAL = 19
INST_LESS_THAN = 20
INST_GREATER_THAN = 21
INST_NEGATE = 22
INST_LOGIC_NOT = 23
INST_LOGIC_AND = 24
INST_LOGIC_OR = 25

class Instruction:
    _immutable_fields_ = ['opcode', 'operand_int', 'operand_josa_list[*]', 'operand_free_var_list[*]', 'operand_str']

    def __init__(self, opcode):
        self.opcode = opcode
        self.operand_int = 0
        self.operand_josa_list = None
        self.operand_free_var_list = None
        self.operand_str = None
