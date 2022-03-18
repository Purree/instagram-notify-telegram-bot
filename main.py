from Config import Config
from Database import Database
from Instagram import Instagram
from Telegram import Telegram

config = Config()


telegram_token = config.read_from_config("TELEGRAM", "token")

telegram = Telegram(telegram_token)
instagram = Instagram(config.get_all_section_parameters("INSTAGRAM"), telegram)
