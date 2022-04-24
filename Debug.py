from Config import Config
import logging
import os


class Debug:
    debug_state = False

    def __init__(self, debug_state=Config().read_from_config("DEBUG", "debug")):
        if (type(debug_state) == bool and debug_state) or (type(debug_state) == str and debug_state.lower() == "true"):
            self.debug_state = True

        file_name = './logs/app.log'
        if not os.path.exists(file_name):
            os.makedirs("/".join(file_name.split('/')[:-1]))
            with open(file_name, 'w'): pass

        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filename=file_name)

    def dump(self, *params):
        if self.debug_state:
            print(*params)
            logging.debug(*params)

    def dump_and_die(self, value):
        if self.debug_state:
            raise Exception(value)

    def error_handler(self, *error):
        print("\033[91m {}\033[00m".format("".join(str(error))))
        logging.critical(error, exc_info=True)
