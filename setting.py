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
            "block_indent": args[5],
            "var_declaration_indent": args[6],
            "begin_indent": args[7]
        }

        self.lines = {
            "max_line_length": args[8]
        }

