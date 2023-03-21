from setting import Setting


class Linter:
    def __init__(self):
        self.setting = Setting()
        self.check_code = {
            "variable_name": self.check_variables,
            "class_name": self.check_classes,
            "function_name": self.check_functions,
            "level_indent": self.check_level_indent,
            "block_indent": self.check_block_indent,
            "operator_indent": self.check_operator_indent,
            "var_declaration_indent": self.check_var_indent,
            "max_line_length": self.check_max_line_length,
            "check_comments": self.check_check_comments,
            "begin_indent": self.check_begin_indent
        }

    def set_setting(self, rules: Setting):
        self.setting = rules

    def process_code(self, file):
        return 0