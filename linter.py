import re
from enum import Enum

from errors import Error_Linter
from setting import Setting
from Token import Token, TypeToken
from tokenizer import Tokenizer


def get_re_style(s: str):
    if s == "snake":
        return r'^[a-z][a-z0-9]+(?:_[a-z0-9]+)*$'
    if s == "usnake":
        return r'^[A-Z]+(?:_[A-Z0-9]+)*$'
    if s == "camel":
        return r'^[a-z]+(?:[A-Z][a-z0-9]+)*$'
    if s == "ucamel":
        return r'^[A-Z][a-zA-Z0-9]*$'


def print_error(e, line):
    print(f'{e}, строка: {str(line)}')


def check_expr_indent(tokens, nesting):
    new_tokens = []
    for_process_br = []
    for_process_expr = []
    l_brackets = [TypeToken.L_PAREN, TypeToken.L_BRACKET]
    r_brackets = [TypeToken.R_PAREN, TypeToken.R_BRACKET]

    admit = [
        TypeToken.NAME, TypeToken.NUMBER, TypeToken.STRING,
        TypeToken.EXPRESSION, TypeToken.BRACKETS,
        TypeToken.OP_MATH, TypeToken.OP_LOGIC,
        TypeToken.OP_ASSIGN, TypeToken.OP_COMPARE
    ]

    admit_br = [
        TypeToken.NAME, TypeToken.NUMBER, TypeToken.STRING,
        TypeToken.EXPRESSION, TypeToken.BRACKETS,
        TypeToken.COMMA, TypeToken.DIAPASON,
        TypeToken.OP_MATH, TypeToken.OP_LOGIC,
        TypeToken.OP_ASSIGN, TypeToken.OP_COMPARE
    ]

    first_brackets = None
    last_brackets = None
    last_token = None

    for token in tokens:
        if token.type in l_brackets:
            if nesting and first_brackets is None:
                first_brackets = token
                continue
            for_process_br.append([token])

        elif token.type in r_brackets:
            if len(for_process_br) > 0:
                if last_token.type is TypeToken.SPACE:
                    print_error("Лишний пробел перед закрывающей скобкой",
                                last_token.line)

                for_process_br[-1].append(token)
                expr_br = check_expr_indent(for_process_br.pop(), True)
                expr_br.add_interior_tokens(for_process_br)
                for_process_expr.append(expr_br)
            else:
                if nesting and last_brackets is None:
                    last_brackets = token
                    last_token = token
                    continue
                print_error("Лишняя закрывающая скобка", token.line)

        elif token.type is TypeToken.SPACE:
            last_token = token
            if len(for_process_br) > 0:
                if len(for_process_br[-1]) == 1:
                    print_error("Лишний пробел после открывающей скобки",
                                token.line)
                    continue
                for_process_br[-1].append(token)
                continue
            if len(for_process_expr) > 0:
                for_process_expr.append(token)
                if len(token.value) > 1:
                    print_error("Слишком много пробелов",
                                token.line)
            else:
                new_tokens.append(token)
            continue

        elif len(for_process_br) == 0:
            if token.type in admit:
                for_process_expr.append(token)
                if last_token is not None:
                    if not(last_token.type in [TypeToken.SPACE, TypeToken.TAB]):
                        print_error("пропущен пробел", last_token.line)
            else:
                if len(for_process_expr) == 1:
                    new_tokens.append(for_process_expr[0])
                if len(for_process_expr) > 1:
                    value = Token.get_values_tokens(for_process_expr)
                    expr = Token(value, TypeToken.EXPRESSION,
                                 for_process_expr[0].line)
                    expr.add_interior_tokens(for_process_expr)
                    new_tokens.append(expr)
                for_process_expr = []
                new_tokens.append(token)
            last_token = token
        else:
            if token.type in admit_br:
                for_process_br[-1].append(token)
            elif token.type in [TypeToken.TAB, TypeToken.NEW_LINE]:
                continue
            else:
                expr = check_expr_indent(for_process_br.pop(), True)
                expr.add_interior_tokens(for_process_br)
                for_process_expr.append(expr)
                value = Token.get_values_tokens(for_process_expr)
                expr = Token(value, TypeToken.EXPRESSION,
                             for_process_expr[0].line)
                expr.add_interior_tokens(for_process_expr)
                new_tokens.append(expr)
                new_tokens.append(token)
            last_token = token

    if nesting:
        upd_tokens = [first_brackets]
        for t in new_tokens:
            upd_tokens.append(t)
        for t2 in for_process_expr:
            upd_tokens.append(t2)
        upd_tokens.append(last_brackets)
        value = Token.get_values_tokens(upd_tokens)
        t = Token(value, TypeToken.EXPRESSION,
                  first_brackets.line)
        t.add_interior_tokens(upd_tokens)
        return t
    else:
        return new_tokens


class Linter:
    def __init__(self):
        self.setting = Setting()
        self.errors = Error_Linter()
        self.tokenizer = Tokenizer()

        self.tokens = []

        self.check_code = {
            "names": self.check_names,
            "poins": self.check_points,
            "expression_indent": self.check_expression_indent,
            "punctuation_indent": self.punctuation_indent,
            #"var_declaration_indent": self.check_var_indent,
            #"level_indent": self.check_level_indent,
            #"block_indent": self.check_block_indent,
            #"begin_indent": self.check_begin_indent,
            #"max_line_length": self.check_max_line_length,
            #"check_comments": self.check_check_comments
        }

    def set_setting(self, rules: Setting):
        self.setting = rules

    def process_code(self, file):
        code = Linter.reading_file(file)
        self.tokens = self.tokenizer.get_tokens_from_file(code)
        self.sort_name_tokens()
        for check_name, check_function in self.check_code.items():
            print("Checking " + check_name)
            check_function()
            a = 0
        return 0

    @staticmethod
    def reading_file(file_name):
        s = []
        for line in file_name:
            s.append(line)
        return s

    def sort_name_tokens(self):
        names = self.tokenizer.sort_name_tokens(self.tokens)
        self.var_names = names[0]
        self.class_names = names[1]
        self.const_names = names[2]
        self.function_names = names[3]
        self.reserved_name = names[4]

    def check_names(self):
        self.check_that_names(self.var_names, self.setting.names["variable_name"])
        self.check_that_names(self.class_names, self.setting.names["class_name"])
        self.check_that_names(self.const_names, self.setting.names["const_name"])
        self.check_that_names(self.function_names, self.setting.names["function_name"])
        self.check_that_names(self.reserved_name, self.setting.names["reserved_name"])

    def check_that_names(self, names, setting):
        re_pattern = get_re_style(setting)
        re_obj = re.compile(re_pattern)
        for token in names:
            if not re_obj.match(token.value):
                e = "Неправильный стиль именнования переменной: " + token.value
                print_error(e, token.line)

    def check_points(self):
        self.union_diapason(TypeToken.NUMBER)
        self.union_diapason(TypeToken.STRING)
        self.union_name_point_field()

    def union_diapason(self, type_token):
        new_tokens = []
        diapason = []

        for token in self.tokens:
            if token.type is type_token:
                if token.type_num == "float":
                    if len(diapason) == 3:
                        print_error("Числа в диапазоне должны быть целыми", token.line)
                        for t in diapason:
                            new_tokens.append(t)
                        diapason = []
                    last = token
                    new_tokens.append(token)
                    continue
                if len(diapason) == 0:
                    diapason.append(token)
                if len(diapason) == 2:
                    print_error("Пропущена точка", token.line)
                    diapason.append(token)
                elif len(diapason) == 3:
                    if diapason[0].value > token.value:
                        print_error("Первое значение в диапазоне должно быть меньше", token.line)
                    diapason.append(token)
            elif token.type is TypeToken.NAME:
                if token.value in self.const_names:
                    if len(diapason) == 0 or len(diapason) == 3:
                        diapason.append(token)
                        last = token
                        continue
                elif len(diapason) == 3:
                    print_error("Должна быть констанста", token.line)
                for t in diapason:
                    new_tokens.append(t)
                new_tokens.append(token)
                diapason = []
            elif token.type is TypeToken.POINT:
                if len(diapason) in [1, 2]:
                    diapason.append(token)
                elif len(diapason) > 2:
                    print_error("Лишняя точка", token.line)
                else:
                    new_tokens.append(token)
            else:
                if len(diapason) == 4:
                    t = Token(Token.get_values_tokens(diapason), TypeToken.DIAPASON, diapason[0].line)
                    new_tokens.append(t)
                else:
                    for t in diapason:
                        new_tokens.append(t)
                new_tokens.append(token)
                diapason = []

        self.tokens = new_tokens

    def union_name_point_field(self):
        # дополнительно объединяет переменные с их полями в одну переменную
        fl_point = None
        last = None
        new_tokens = []
        new_token = []

        for token in self.tokens:
            if token.type is TypeToken.NAME:
                new_token.append(token)
                fl_point = None
            elif token.type is TypeToken.POINT:
                if len(new_token) == 0:
                    if last.value.lower() != 'end':
                        print_error("Ожидалось имя перед точкой", token.line)
                elif new_token[-1].type == TypeToken.POINT:
                    print_error("Ожидалось имя перед точкой", token.line)
                else:
                    fl_point = token
                    new_token.append(token)
            else:
                if fl_point is not None:
                    print_error("Лишняя точка", token.line)
                    new_token.remove(fl_point)
                if len(new_token) > 0:
                    t = Token(Token.get_values_tokens(new_token), TypeToken.NAME, new_token[0].line)
                    t.add_interior_tokens(new_token)
                    new_token = []
                    new_tokens.append(t)
                last = token
                new_tokens.append(token)

        self.tokens = new_tokens

    def check_expression_indent(self):
        self.tokens = check_expr_indent(self.tokens, False)

    def punctuation_indent(self):
        last_token = None
        indents = [TypeToken.TAB, TypeToken.SPACE, TypeToken.NEW_LINE]
        delimiters = [TypeToken.SEMICOLON, TypeToken.COLON, TypeToken.COMMA]

        for token in self.tokens:
            if token.type in delimiters:
                if last_token.type in indents:
                    print_error("Лишний пробел перед разделителем", token.line)
            elif token.type in [TypeToken.TAB, TypeToken.SPACE]:
                if last_token.type is TypeToken.SEMICOLON:
                    print_error("Лишние пробелы после ; ", token.line)
                elif last_token.type in [TypeToken.COLON, TypeToken.COMMA]:
                    if len(token.value) > 1:
                        print_error("Слишком много пробелов после разделителя", token.line)
            elif token.type is TypeToken.NEW_LINE:
                if last_token.type in [TypeToken.COLON, TypeToken.COMMA]:
                    print_error("Неожиданный перенос после разделителя", token.line)
            last_token = token
