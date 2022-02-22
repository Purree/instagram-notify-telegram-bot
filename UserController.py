from Database import Database
from Config import Config


class UserController:
    def __init__(self):
        self.database = Database(Config().get_all_section_parameters('DATABASE'))

    def create_new_user(self, telegram_id):
        self.database.add_new_user(telegram_id)
