class Setting:
    def __init__(self, args=None):
        if args is None:
            args = [0 for i in range(9)]
        self.variable_name = ["variable_name", args[0]]
        self.class_name = ["class_name", args[1]]
        self.function_name = ["function_name", args[2]]
        self.level_indent = ["level_indent", args[3]]
        self.block_indent = ["block_indent", args[4]]
        self.operator_indent = ["operator_indent", args[5]]
        self.var_declaration_indent = ["var_declaration_indent", args[6]]
        self.max_line_length = ["max_line_length", args[7]]
        self.check_comments = ["check_comments", 0]
        self.begin_indent = ["begin_indent", args[8]]
