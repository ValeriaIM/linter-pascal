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


class Linter:
    def __init__(self):
        self.setting = Setting()
        self.errors = Error_Linter()
        self.tokenizer = Tokenizer()

        self.tokens = []

        self.check_code = {
            "names": self.check_names,
            "poins": self.check_points,
            "operator_indent": self.check_all_operator_indent,
            "punctuation_indent": self.punctuation_indent,
            "brackets_indent": self.check_brackets_indent
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

    def check_all_operator_indent(self):
        self.check_operator_indent(TypeToken.OP_MATH)
        self.check_operator_indent(TypeToken.OP_COMPARE)
        self.check_operator_indent(TypeToken.OP_LOGIC)
        self.check_operator_indent(TypeToken.OP_ASSIGN)

    def check_operator_indent(self, type_op):
        fl_space = None
        fl_op = False
        op = None
        ind = int(self.setting.indents["operator_indent"])

        exp = []
        new_tokens = []
        err = None

        if isinstance(self.tokens, list):
            #без этого вылетает странная ошибка, которой нет при дебаге
            for token in self.tokens:
                if token.type in [TypeToken.NAME, TypeToken.EXPRESSION, TypeToken.NUMBER]:
                    if len(exp) > 0:
                        if fl_op:
                            if fl_space is None and ind != 0:
                                print_error("Пропущен пробел перед переменной", token.line)
                            if fl_space is not None and err is not None:
                                print(err, fl_space.line)
                        else:
                            print_error("Пропущен либо разделитель, либо оператор")
                            for t in exp:
                                new_tokens.append(t)
                            exp = []
                    err = None
                    exp.append(token)
                    fl_space = None
                    op = None
                elif token.type is TypeToken.SPACE:
                    if len(exp) > 0:
                        if len(token.value) < ind:
                            err = "Не хватает пробела"
                        if len(token.value) > ind:
                            err = "Лишние пробелы"
                        exp.append(token)
                        fl_space = token
                        op = None
                        continue
                    fl_space = token
                    op = None
                    new_tokens.append(token)
                elif token.type is type_op:
                    if len(exp) == 0:
                        print_error("Пропущена переменная перед оператором", token.line)
                    elif exp[-1].type is type_op:
                        print_error("Пропущена переменная перед оператором", token.line)
                    elif fl_space is None and ind != 0:
                        print_error("Пропущен пробел перед оператором", token.line)
                    elif fl_space is not None and err is not None:
                        print(err, fl_space.line)
                        err = None
                    op = token
                    fl_op = True
                    fl_space = None
                    exp.append(token)
                else:
                    if op is not None:
                        print_error("Лишний оператор", token.line)
                        exp.remove(op)
                    if len(exp) > 1:
                        if fl_space is not None:
                            exp.remove(fl_space)
                        t = Token(Token.get_values_tokens(exp), TypeToken.EXPRESSION, exp[0].line)
                        t.add_interior_tokens(exp)
                        new_tokens.append(t)
                        if fl_space:
                            new_tokens.append(fl_space)
                    else:
                        if len(exp) == 1:
                            new_tokens.append(exp[0])
                    exp = []
                    op = None
                    fl_space = None
                    fl_op = False
                    new_tokens.append(token)

        self.tokens = new_tokens

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

    def check_brackets_indent(self):
        inside_brackets = []
        l_brackets = []
        new_tokens = []

        for token in self.tokens:
            if token.type in [TypeToken.L_BRACKET, TypeToken.L_PAREN]:
                inside_brackets.append([token])
                l_brackets.append(token)
            elif token.type in [TypeToken.R_BRACKET, TypeToken.R_PAREN]:
                if len(l_brackets) > 0:
                    last = l_brackets.pop()
                    is_both_bracket = (last.type == TypeToken.L_BRACKET and
                                       token.type == TypeToken.R_BRACKET)
                    is_both_paren = (last.type == TypeToken.L_PAREN and
                                     token.type == TypeToken.R_PAREN)
                    if not is_both_paren and not is_both_bracket:
                        print_error("Неправильный порядок скобок", token.line)
                        self.process_r_bracket(inside_brackets, None, new_tokens)
                    else:
                        self.process_r_bracket(inside_brackets, token, new_tokens)
                else:
                    print_error("Лишняя закрывающая квадратная скобка", token.line)

            elif token.type in [TypeToken.SEMICOLON, TypeToken.RESERVED]:
                if len(l_brackets) > 0:
                    self.process_too_many_brackets(inside_brackets, token, new_tokens)
                else:
                    new_tokens.append(token)
            elif token.type is TypeToken.SPACE:
                if len(inside_brackets) > 0:
                    if len(inside_brackets[-1]) == 1:
                        print_error("Лишний пробел после открывающей скобки", token.line)
                    inside_brackets[-1].append(token)
                else:
                    new_tokens.append(token)
            elif len(inside_brackets) > 0:
                inside_brackets[-1].append(token)
            else:
                new_tokens.append(token)

        self.tokens = new_tokens

    @staticmethod
    def process_too_many_brackets(inside_brackets, token, new_tokens):
        print_error("Не хватает закрывающих квадратных скобок", token.line)
        while len(inside_brackets) > 0:
            bracket = inside_brackets.pop()
            t = Token(Token.get_values_tokens(bracket), TypeToken.BRACKETS, bracket[0].line)
            t.add_interior_tokens(bracket)
            if len(inside_brackets) > 0:
                inside_brackets[-1].append(t)
            else:
                new_tokens.append(t)

    @staticmethod
    def process_r_bracket(inside_brackets, token, new_tokens):
        if inside_brackets[-1][-1].type is TypeToken.SPACE:
            print_error("Лишний пробел", token.line)
            inside_brackets[-1].pop()
        if token:
            inside_brackets[-1].append(token)
        bracket = inside_brackets.pop()
        t = Token(Token.get_values_tokens(bracket), TypeToken.BRACKETS, bracket[0].line)
        t.add_interior_tokens(bracket)
        if len(inside_brackets) > 0:
            inside_brackets[-1].append(t)
        else:
            new_tokens.append(t)
