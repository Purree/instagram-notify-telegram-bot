from Config import Config
from Database import Database
from Instagram import Instagram
from Telegram import Telegram

config = Config()
instagram = Instagram(config.get_all_section_parameters("INSTAGRAM"))

telegram_token = config.read_from_config("TELEGRAM", "token")
database_parameters = config.get_all_section_parameters("DATABASE")

database = Database(database_parameters)
telegram = Telegram(telegram_token)
