class Error_Linter:
    def __init__(self):
        self.error_names = {
            "A000": "Name is not valid",
            "A001": "Name should be in snake-case",
            "A002": "Name should be in camel-case",
            "A003": "Name should be in upper camel-case",
        }

        self.error_indent = {
            "B000": "Too many lines",
            "B001": "Too many spaces between level",
            "B002": "Space has been missing between level",
            "B011": "Too many lines before blocks",
            "B012": "Too many lines after blocks",
            "B013": "Line has been missing before blocks",
            "B014": "Line has been missing after blocks",
            "B021": "Too many spaces between name/var and operator",
            "B022": "Space has been missing between name/var and operator",
            "B031": "Too many lines after var declaration",
            "B032": "Line after var declaration has been missing",
            "B041": "Line before begin has been missing"
        }

        self.error_lines = {
            "C001": "Line is too long",
            "C010": "Last line has been missing",
            "C011": "Too many lines was in the end"
        }
