import threading

from Config import Config
from Debug import Debug
from Telegram import Telegram


def excepthook(args):
    Debug().error_handler(args)


if __name__ == "__main__":
    print('Start script')

    try:

        threading.excepthook = excepthook

        config = Config()

        telegram_token = config.read_from_config("TELEGRAM", "token")
        telegram = Telegram(telegram_token)

    except Exception as e:
        excepthook(e)
