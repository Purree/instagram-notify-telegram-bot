import distutils

from Config import Config


class Debug:
    debug_state = False

    def __init__(self, debug_state=Config().read_from_config("DEBUG", "debug")):
        if (type(debug_state) == bool and debug_state) or (type(debug_state) == str and debug_state.lower() == "true"):
            self.debug_state = True

    def dump(self, *params):
        if self.debug_state:
            print(*params)

    def dump_and_die(self, value):
        if self.debug_state:
            raise Exception(value)
