from enum import Enum


class TypeToken(Enum):
    COMMENT = "COMMENT"
    STRING = "STRING"
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"
    OP_ASSIGN = "OP_ASSIGN"
    OP_LOGIC = "OP_LOGIC"
    OP_COMPARE = "OP_COMPARE"
    OP_MATH = "OP_MATH"
    L_PAREN = "L_PAREN"
    R_PAREN = "R_PAREN"
    L_BRACKET = "L_BRACKET"
    R_BRACKET = "R_BRACKET"
    BRACKETS = "BRACKETS"
    SEMICOLON = "SEMICOLON"
    COLON = "COLON"
    POINT = "POINT"
    COMMA = "COMMA"
    TAB = "TAB"
    SPACE = "SPACE"
    NEW_LINE = "NEW_LINE"
    RESERVED = "RESERVED"
    NAME = "NAME"
    EXPRESSION = "EXPRESSION"
    DECLARATION = "DECLARATION"
    TYPE = "TYPE"
    ARRAY = "ARRAY"
    BLOCK = "BLOCK"
    DIAPASON = "DIAPASON"


class Token:
    def __init__(self, val: str, t, n):
        self.value = val
        self.type = t
        if isinstance(t, str):
            self.type = self.get_type(t)
        self.line = n
        self.tokens = []
        self.type_num = None
        self.visibility = None

    def __str__(self):
        str_token = self.type.value
        str_token += f'|{self.value}|'
        str_token += f'|{str(self.line)}|'
        return str_token

    def __repr__(self):
        return str(self)

    @staticmethod
    def get_type(t: str):
        for token in TypeToken.__members__.values():
            if token.value == t:
                return token
        return TypeToken.IDENTIFIER

    def set_type_num(self, type_num: str):
        if self.type is TypeToken.NUMBER:
            self.type_num = type_num

    def set_visibility(self, area):
        self.visibility = area

    def add_interior_tokens(self, tokens):
        self.tokens = tokens

    @staticmethod
    def get_values_tokens(tokens):
        s = ""
        for token in tokens:
            s += token.value
        return s

    @staticmethod
    def get_token_from_list(tokens: list, type_t):
        value = Token.get_values_tokens(tokens)
        t = Token(value, type_t, tokens[0].line)
        t.add_interior_tokens(tokens)
        return t