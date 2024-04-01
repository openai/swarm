class Context:
    def __init__(self):
        self.variables = {}

    def set_variable(self, key, value):
        self.variables[key] = value

    def get_variable(self, key):
        return self.variables.get(key)

    def clear(self):
        self.variables.clear()
