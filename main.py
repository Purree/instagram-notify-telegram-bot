from Config import Config
from Debug import Debug
from Telegram import Telegram

if __name__ == "__main__":
    print('Start script')

    try:
        config = Config()

        telegram_token = config.read_from_config("TELEGRAM", "token")
        telegram = Telegram(telegram_token)

    except Exception as e:
        Debug().error_handler(e)
