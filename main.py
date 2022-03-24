from Config import Config
from Telegram import Telegram

config = Config()


telegram_token = config.read_from_config("TELEGRAM", "token")

telegram = Telegram(telegram_token)
