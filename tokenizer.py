import configparser
import re
from Token import Token, TypeToken


class Tokenizer:
    def __init__(self):
        self.base_tokens = []
        self.reserved_tokens = {}
        self.signs = {}
        self.with_delimiter = []
        self.without_punctuation = []
        self.info = {}
        self.set_reserved_words('reserved_tokens.ini')

    def get_tokens_from_file(self, code):
        tokens = []
        operators_assign = r"\+=|\*=|\+\+|/=|--|-=|:=|="
        operators_compare = r">=|<=|!=|==|>|<"
        operators_math = r"\+|-|\*|/"
        num = r'-?(?:\$)?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
        comment = r'\{(?:.|\n)*?\}|\(\*(?:.|\n)*?\*\)|\/\/.*'
        identifier = r'[a-zA-Z_а-яА-Я][a-zA-Z0-9_]*[а-яА-Я0-9]*'

        token_specification = [
            ("COMMENT", comment),  # Комментарии
            ("STRING", r'\'[^\']*\'|"[^"]*"'),  # Строковые литералы
            ("NUMBER", num),  # Числа
            ("IDENTIFIER", identifier),  # Идентификаторы
            ("L_PAREN", r'\('),  # Левая скобка
            ("R_PAREN", r'\)'),  # Правая скобка
            ("L_BRACKET", r'\['),  # Левая скобка
            ("R_BRACKET", r'\]'),  # Правая скобка
            ("SEMICOLON", r';'),  # Точка с запятой
            ("OP_ASSIGN", operators_assign),  # Присваивание
            ("OP_COMPARE", operators_compare),  # Сравнение
            ("OP_MATH", operators_math),  # Арифм. операции
            ("COLON", r':'),  # Двоеточие
            ("POINT", r'\.'),  # Запятая
            ("COMMA", r','),  # Запятая
            ("TAB", r'[\t]+'),  # табы
            ("SPACE", r'[ ]+'),  # пробелы
            ("NEW_LINE", r'[\n]+'),  # переносы
        ]

        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        line = 1
        comments = []

        for str_code in code:
            for mo in re.finditer(tok_regex, str_code):
                if mo.lastgroup == "NEW_LINE":
                    line += 1
                t_type = mo.lastgroup

                if t_type == "COMMENT":
                    com = mo.group(0).split('\n')
                    token = self.create_token(t_type, com[0], line)
                    comments.append(token)
                    if len(com) > 1:
                        token = self.create_token("NEW_LINE", com[1], line)
                        tokens.append(token)
                else:
                    token = self.create_token(t_type, mo.group(0), line)
                    if token.type is TypeToken.COMMENT:
                        comments.append(token)
                    else:
                        tokens.append(token)

        return tokens, comments

    def create_token(self, token_type, token_value, line):
        if token_type == "NUMBER":
            t = Token(token_value, token_type, line)
            if token_value.isdigit():
                t.set_type_num("int")
                return t
            t.set_type_num("float")
            return t
        if token_type != "IDENTIFIER":
            return Token(token_value, token_type, line)
        if token_value.lower() in self.base_tokens:
            if token_value.lower() in self.reserved_tokens["math_operator"]:
                return Token(token_value, TypeToken.OP_MATH, line)
            if token_value.lower() in self.reserved_tokens["logic_operator"]:
                return Token(token_value, TypeToken.OP_LOGIC, line)
            if token_value.lower() in self.reserved_tokens["types"]:
                return Token(token_value, TypeToken.TYPE, line)
            return Token(token_value, TypeToken.RESERVED, line)
        return Token(token_value, TypeToken.NAME, line)

    def sort_name_tokens(self, tokens):
        var_names = []
        class_names = []
        const_names = []
        function_names = []
        record_names = []
        reserved_name = []
        fl_declaration = False
        type_declaration = None
        func = None

        for token in tokens:
            if token.type is TypeToken.RESERVED:
                reserved_name.append(token)
                if token.value.lower() in self.reserved_tokens["declaration"]:
                    fl_declaration = True
                    type_declaration = token.value
                elif token.value.lower() in self.reserved_tokens["code_block_delimiter"]:
                    if token.value.lower() == "end":
                        func = None
                    fl_declaration = False
            elif fl_declaration:
                if token.type is TypeToken.NAME:
                    if type_declaration.lower() == "var":
                        token.set_visibility(func)
                        var_names.append(token)
                    elif type_declaration.lower() == "type":
                        token.set_visibility(func)
                        class_names.append(token)
                    elif type_declaration.lower() == "const":
                        token.set_visibility(func)
                        const_names.append(token)
                    elif type_declaration.lower() == "record":
                        token.set_visibility(func)
                        record_names.append(token)
                    else:
                        func = token
                        function_names.append(token)

        return [var_names, class_names, const_names,
                function_names, reserved_name, record_names]

    def set_reserved_words(self, file_name):
        config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
        config.read(file_name)

        if 'RESERVED' in config:
            reserved = config['RESERVED']
            for key, value in reserved.items():
                tokens = [t.strip() for t in value.split(',')]
                self.reserved_tokens[key] = tokens
                for token in tokens:
                    self.base_tokens.append(token)
        else:
            print("Can't find reserved tokens")
            raise KeyError("В файле reserved_tokens.ini не хватает раздела")

        if 'SIGNS' in config:
            signs = config['SIGNS']
            for key, value in signs.items():
                tokens = [t.strip() for t in value.split(',')]
                self.signs[key] = tokens
                for token in tokens:
                    self.base_tokens.append(token)
        else:
            print("Can't find SIGNS tokens")
            raise KeyError("В файле reserved_tokens.ini не хватает раздела")

        if 'INFO' in config:
            info = config['INFO']

            for key, value in info.items():
                if key == "with_delimiter":
                    self.with_delimiter = [t.strip() for t in value.split(',')]
                elif key == "without_punctuation":
                    self.without_punctuation = [t.strip() for t in value.split(',')]
                else:
                    self.info[key] = [t.strip() for t in value.split(',')]
        else:
            print("Can't find INFO tokens")
            raise KeyError("В файле reserved_tokens.ini не хватает раздела")
