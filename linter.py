import re

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
        TypeToken.TYPE, TypeToken.ARRAY,
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
                    if not (last_token.type in [TypeToken.SPACE, TypeToken.TAB]):
                        print_error("пропущен пробел", last_token.line)
            else:
                if len(for_process_expr) == 1:
                    new_tokens.append(for_process_expr[0])
                if len(for_process_expr) > 1:
                    expr = Token.get_token(for_process_expr,
                                           TypeToken.EXPRESSION)
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
                expr = Token.get_token(for_process_expr,
                                       TypeToken.EXPRESSION)
                new_tokens.append(expr)
                new_tokens.append(token)
            last_token = token

    if nesting:
        upd_tokens = [first_brackets]
        upd_tokens.extend(new_tokens)
        upd_tokens.extend(for_process_expr)
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
        self.comments = []

        self.check_code = {
            "max_line_length": self.check_max_line_length,
            "names": self.check_names,
            "points": self.check_points,
            "var_declaration_indent": self.check_var_indent,
            "expression_indent": self.check_expression_indent,
            "punctuation_indent": self.punctuation_indent,
            "check_end_else_punct": self.check_end_else_punct,
            "check_tab": self.check_tab,
            "process_blocks": self.process_blocks
        }

    def set_setting(self, rules: Setting):
        self.setting = rules

    def process_code(self, file):
        code = Linter.reading_file(file)
        self.tokens, self.comments = self.tokenizer.get_tokens_from_file(code)
        self.sort_name_tokens()
        for check_name, check_function in self.check_code.items():
            #print("Checking " + check_name)
            check_function()
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
        self.record_names = names[5]
        decl_name = []
        decl_name.extend(names[0])
        decl_name.extend(names[1])
        decl_name.extend(names[2])
        decl_name.extend(names[3])
        decl_name.extend(names[5])
        self.decl_name = decl_name

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
                e = "Неправильный стиль написания идентификатора: " + token.value
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
                        new_tokens.extend(diapason)
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
                new_tokens.extend(diapason)
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
                    new_tokens.extend(diapason)
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

    def check_type_array(self):
        new_type = []
        fl_array = 0
        last_token = None
        new_tokens = []

        for token in self.tokens:
            if token.type is TypeToken.TYPE:
                if token.value.lower() == "array":
                    new_type.append(token)
                    fl_array = 1
                    last_token = token
                    continue
                if token.value.lower() == "of":
                    if fl_array == 1 or fl_array == 4:
                        self.check_space_token(last_token, 1)
                        new_type.append(token)
                        fl_array = 5
                    elif fl_array > 1 and fl_array != 4:
                        print_error("Неверно стоит of", token.line)
                    else:
                        new_tokens.append(token)
                    continue
                else:
                    if fl_array == 5:
                        self.check_space_token(last_token, 1)
                        new_type.append(token)
                        t = Token.get_token(new_type, TypeToken.ARRAY)
                        new_tokens.append(t)
                        new_type = []
                        fl_array = 0
                    else:
                        new_tokens.append(token)
            elif token.type is TypeToken.SPACE:
                if fl_array > 0:
                    new_type.append(token)
                    last_token = token
                else:
                    new_tokens.append(token)
            elif token.type is TypeToken.L_BRACKET:
                fl_array = self.put_interval_init(new_type, [fl_array, 1, 2],
                                                  token, last_token, new_tokens, 1)
                last_token = token
            elif token.type is TypeToken.DIAPASON:
                fl_array = self.put_interval_init(new_type, [fl_array, 2, 3],
                                                  token, last_token, new_tokens, 0)
                last_token = token
            elif token.type is TypeToken.R_BRACKET:
                fl_array = self.put_interval_init(new_type, [fl_array, 3, 4],
                                                  token, last_token, new_tokens, 0)
                last_token = token
            else:
                if len(new_type) > 0:
                    print_error("Неожиданный токен в объявлении массива", token.line)
                    t = Token.get_token(new_type, TypeToken.ARRAY)
                    new_tokens.append(t)
                new_tokens.append(token)
        self.tokens = new_tokens

    def put_interval_init(self, new_type, fls: list, token, last_token, tokens, i):
        fl_array = fls[0]
        fl_eq = fls[1]
        fl_set = fls[2]

        if fl_array == fl_eq:
            self.check_space_token(last_token, i)
            new_type.append(token)
            fl_array = fl_set
        elif fl_array > 1:
            print_error("Сначала пишется интервал", token.line)
        else:
            tokens.append(token)
        return fl_array

    def check_var_indent(self):
        self.check_type_array()

        new_decl = []
        fl_decl = 0
        new_tokens = []

        if isinstance(self.tokens, list):
            for token in self.tokens:
                if token in self.var_names or token in self.record_names:
                    fl_decl = 1
                    new_decl.append(token)
                    continue
                if token.type is TypeToken.SPACE:
                    if fl_decl == 1:
                        print_error("Лишний пробел перед :", token.line)
                    if fl_decl > 0:
                        new_decl.append(token)
                    else:
                        new_tokens.append(token)
                    continue
                if token.type is TypeToken.COLON:
                    if fl_decl == 1:
                        new_decl.append(token)
                        fl_decl = 2
                    else:
                        new_tokens.append(token)
                    continue
                if self.is_type(token):
                    if fl_decl == 2:
                        new_decl.append(token)
                        t = Token.get_token(new_decl, TypeToken.DECLARATION)
                        new_tokens.append(t)
                        fl_decl = 0
                        new_decl = []
                    else:
                        new_tokens.append(token)
                    continue
                if fl_decl > 0:
                    if token in self.decl_name:
                        print_error("Ожидался тип/класс", token.line)
                        new_decl.append(token)
                    else:
                        print_error("Неожиданный символ в объявлении", token.line)
                    t = Token.get_token(new_decl, TypeToken.DECLARATION)
                    new_tokens.append(t)
                    fl_decl = 0
                    new_decl = []
                    new_tokens.append(token)
                else:
                    new_tokens.append(token)

        self.tokens = new_tokens

    def is_type(self, token):
        if token.type is TypeToken.TYPE:
            return True
        if token.type is TypeToken.ARRAY:
            return True
        if token in self.class_names:
            return True
        return False

    def check_tab(self):
        lvl = 0
        fl_temp = False
        fl_temp_begin = 0
        is_first = True
        last_reserved = None
        last_tab = None
        first_begin = None

        for token in self.tokens:
            if token.type is TypeToken.TAB:
                last_tab = token
                continue
            if token.type is TypeToken.RESERVED:
                last_reserved = token
                if token.value.lower() == "begin" and first_begin is None:
                    first_begin = token
                    lvl -= 1
            if is_first:
                is_first = False
                if token.value.lower() in self.tokenizer.info["down_lvl"] and lvl > 0:
                    lvl -= 1
                if last_tab is None and lvl > 0:
                    print_error("Ошибка табуляции", token.line)
                if last_tab is not None:
                    if len(last_tab.value) != lvl:
                        print_error("Ошибка табуляции", token.line)
                if token.type is TypeToken.SPACE:
                    print_error("Пробел в начале строки", token.line)
                if fl_temp:
                    if token.value.lower() == "begin":
                        fl_temp_begin += 1
                    if token.value.lower() == "end":
                        fl_temp_begin -= 1
                    if fl_temp_begin == 0:
                        fl_temp = False
                        lvl -= 1

                continue
            if token.type is TypeToken.NEW_LINE:
                is_first = True
                last_tab = None
                if last_reserved is None:
                    continue
                if last_reserved.value.lower() in self.tokenizer.info["up_lvl"]:
                    lvl += 1
                    last_reserved = None
                    continue
                if last_reserved.value.lower() in self.tokenizer.info["temp_up_lvl"]:
                    lvl += 1
                    fl_temp = True
                    last_reserved = None
                    continue

    @staticmethod
    def check_space_token(token, indent):
        if token.type is TypeToken.SPACE:
            if len(token.value) > indent:
                print_error("Слишком много пробелов", token.line)
        else:
            if indent != 0:
                print_error("Пропущен пробел", token.line)

    def punctuation_indent(self):
        last_token = None
        indents = [TypeToken.TAB, TypeToken.SPACE, TypeToken.NEW_LINE]
        delimiters = [TypeToken.SEMICOLON, TypeToken.COLON, TypeToken.COMMA]
        without_delimiters = ["if", "for", "to", "while", "then"]
        last_expr = None
        last_reserved = None

        for token in self.tokens:
            if token.type is TypeToken.RESERVED:
                last_reserved = token
                last_expr = None
            if token.type in [TypeToken.EXPRESSION, TypeToken.DECLARATION]:
                last_expr = token
            if token.type in delimiters:
                if last_token.type in indents:
                    print_error("Лишний пробел перед разделителем", token.line)
                    continue
                if last_expr and last_reserved:
                    if last_reserved.value.lower() in without_delimiters:
                        print_error("Лишний разделитель", token.line)
                if last_expr is None and last_reserved:
                    if last_reserved.value.lower() != "end":
                        print_error("Лишний разделитель", token.line)
                last_expr = None
                last_reserved = None
            elif token.type in [TypeToken.TAB, TypeToken.SPACE]:
                if last_token:
                    if last_token.type in delimiters:
                        if len(token.value) > 1:
                            print_error("Слишком много пробелов после разделителя", token.line)
            elif token.type is TypeToken.NEW_LINE:
                if last_expr:
                    if last_reserved:
                        if not last_reserved.value.lower() in without_delimiters:
                            print_error("Пропущена ;", token.line - 1)
                    else:
                        print_error("Пропущена ;", token.line - 1)
                last_expr = None
                if last_token.type in [TypeToken.COLON]:
                    print_error("Неожиданный перенос после :", token.line)
            last_token = token

    def check_end_else_punct(self):
        last_end = None
        last_semicolon = None
        last_token = None
        is_last = False
        was_else = False
        for token in self.tokens:
            if token.type is TypeToken.SEMICOLON:
                last_semicolon = token
                last_token = token
                if last_end:
                    if last_end.line == token.line:
                        last_end = token
                continue
            elif token.type is TypeToken.NEW_LINE:
                if last_token == last_semicolon:
                    is_last = True
                last_token = token
                continue
            elif token.value.lower() == "end":
                if last_end:
                    if (last_end.type is not TypeToken.SEMICOLON and
                            not was_else and (token.line - last_end.line) != 1):
                        print_error("Пропущена ; после end", last_end.line)

                was_else = False
                last_end = token
                last_token = token
                continue

            elif token.value.lower() == "else":
                was_else = True
                if last_semicolon:
                    if token.line - last_semicolon.line == 1 and is_last:
                        is_last = False
                        print_error("; перед else", last_semicolon.line)

            last_token = token

    def check_max_line_length(self):
        line = 1
        count = 0
        max_c = int(self.setting.lines["max_line_length"])

        for token in self.tokens:
            if token.type is TypeToken.NEW_LINE:
                line += 1
                if count > max_c:
                    print_error("Слишком длинная строка", line)
                count = 0
            else:
                count += len(token.value)

    def process_blocks(self):
        str_empty = []
        last_count = 0
        while len(self.tokens) != last_count:
            last_count = len(self.tokens)
            self.union_expr_in_block()
            self.process_begin_in_blocks()
            self.process_if_blocks()
            str_empty.extend(self.process_empty_lines())

        str_empty = set(str_empty)
        print(str_empty)


    def union_expr_in_block(self):
        new_block = []
        was_expr = False
        new_tokens = []
        admit = [TypeToken.TAB, TypeToken.SPACE,
                 TypeToken.NEW_LINE, TypeToken.SEMICOLON]
        count_expr = 0

        for token in self.tokens:
            if token.type in [TypeToken.EXPRESSION, TypeToken.BLOCK]:
                new_block.append(token)
                was_expr = True
                count_expr += 1
                continue
            elif token.type in admit:
                if was_expr:
                    new_block.append(token)
                else:
                    new_tokens.append(token)
                continue
            else:
                if count_expr > 1:
                    t = Token.get_token(new_block, TypeToken.BLOCK)
                    new_tokens.append(t)
                elif count_expr == 1:
                    new_tokens.extend(new_block)
                new_block = []
                was_expr = False
                count_expr = 0
                new_tokens.append(token)

        if count_expr > 1:
            t = Token.get_token(new_block, TypeToken.BLOCK)
            new_tokens.append(t)
        elif count_expr == 1:
            new_tokens.extend(new_block)

        self.tokens = new_tokens

    def process_if_blocks(self):
        new_block = []
        fl_f = 0
        new_tokens = []
        indent = [TypeToken.TAB, TypeToken.SPACE, TypeToken.NEW_LINE]
        was_indent = False

        for token in self.tokens:
            val = token.value.lower()
            if val == "if":
                if fl_f > 0:
                    new_tokens.extend(new_block)
                fl_f = 1
                new_block.append(token)
                was_indent = False
                continue
            if val == "then":
                was_indent = self.process_was_indent(was_indent, token)
                fl_f = self.process_if_elem(token, new_tokens, new_block, fl_f, [2])
                continue
            if val == "else":
                was_indent = self.process_was_indent(was_indent, token)
                fl_f = self.process_if_elem(token, new_tokens, new_block, fl_f, [4])
                continue
            if token.type in indent:
                if fl_f > 0:
                    new_block.append(token)
                    was_indent = True
                else:
                    new_tokens.append(token)
                continue
            if token.type is TypeToken.EXPRESSION:
                was_indent = self.process_was_indent(was_indent, token)
                fl_f = self.process_if_elem(token, new_tokens, new_block, fl_f, [1, 3, 5])
                continue
            if token.type is TypeToken.BLOCK:
                was_indent = self.process_was_indent(was_indent, token)
                fl_f = self.process_if_elem(token, new_tokens, new_block, fl_f, [3, 5])
                continue
            else:
                if fl_f in [4, 6]:
                    t = Token.get_token(new_block, TypeToken.BLOCK)
                    t.set_type_block("if")
                    new_tokens.append(t)
                    fl_f = 0
                    new_block = []
                    new_tokens.append(token)
                    continue
                if len(new_block) > 0:
                    new_tokens.extend(new_block)
                fl_f = 0
                new_block = []
                new_tokens.append(token)
        self.tokens = new_tokens

    @staticmethod
    def process_was_indent(was_indent, token):
        if not was_indent:
            print_error("Пропущен пробел после if", token.line)
        return False

    @staticmethod
    def process_if_elem(token, new_tokens, new_block, fl_f, i):
        if fl_f in i:
            new_block.append(token)
            fl_f += 1
            return fl_f
        if fl_f > 0:
            print_error(token.type + " не на своем месте", token.line)
            new_block.append(token)
        else:
            new_tokens.append(token)
        return fl_f

    def process_begin_in_blocks(self):
        new_block = []
        new_tokens = []
        admit = [TypeToken.TAB, TypeToken.SPACE,
                 TypeToken.NEW_LINE, TypeToken.SEMICOLON]

        for token in self.tokens:
            val = token.value.lower()
            if val == "begin":
                if len(new_block) > 0:
                    new_tokens.extend(new_block)
                    new_block = []
                new_block.append(token)
                continue
            if token.type in [TypeToken.EXPRESSION, TypeToken.BLOCK]:
                if len(new_block) > 0:
                    new_block.append(token)
                else:
                    new_tokens.append(token)
                continue
            if token.type in admit:
                if len(new_block) > 0:
                    new_block.append(token)
                else:
                    new_tokens.append(token)
                continue
            if val == "end":
                if len(new_block) > 0:
                    new_block.append(token)
                    t = Token.get_token(new_block, TypeToken.BLOCK)
                    new_block = []
                    new_tokens.append(t)
                else:
                    new_tokens.append(token)
            else:
                new_tokens.extend(new_block)
                new_block = []
                new_tokens.append(token)

        self.tokens = new_tokens

    def process_empty_lines(self):
        was_empty_line = []
        is_empty_line = True
        is_first = True
        indents = [TypeToken.TAB, TypeToken.SPACE, TypeToken.NEW_LINE]
        bl_indent = int(self.setting.indents["block_indent"])
        block = ["if"]
        result = []

        for token in self.tokens:
            if token.type is TypeToken.NEW_LINE:
                was_empty_line.append(is_empty_line)
                is_empty_line = True
                is_first = True
            elif token.type in indents:
                continue
            else:
                is_empty_line = False
                if is_first:
                    is_first = False
                    if token.type is TypeToken.BLOCK:
                        if token.type_block in block:
                            lines = was_empty_line[-bl_indent:]
                            for is_empty in lines:
                                if not is_empty:
                                    result.append("Ожидалась пустая строка, строка: " + str(token.line))
                                    break
        return result
