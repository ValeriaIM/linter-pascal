class Setting:
    def __init__(self, args=None):
        if args is None:
            args = [0 for i in range(13)]

        self.names = {
            "variable_name": args[0],
            "class_name": args[1],
            "function_name": args[2],
            "const_name": args[3],
            "reserved_name": args[4]
        }

        self.indents = {
            "level_indent": args[5],
            "block_indent": args[6],
            "operator_indent": args[7],
            "var_declaration_indent": args[8],
            "begin_indent": args[9],
            "comment_indent": args[10]
        }

        self.lines = {
            "max_line_length": args[11]
        }

