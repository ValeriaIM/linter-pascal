from setting import Setting


class Linter:
    def __init__(self):
        self.setting = None

    def set_setting(self, rules):
        self.setting = rules

    def process_code(self, file):
        return 0