from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
import re

from UserController import UserController


class Telegram:
    def __init__(self, token):
        self.updater = Updater(token)
        self.controller = UserController()

        self.main_keyboard_buttons = [['Мои подписки', 'Подписаться']]

        self.activate_handlers()

        self.updater.start_polling()
        self.updater.idle()

    def start_command_handler(self, update: Update, context: CallbackContext) -> None:
        if self.controller.create_new_user(update.message.from_user.id):
            update.message.reply_text("Здравствуйте!", reply_markup=self.generate_keyboard())
        else:
            update.message.reply_text("И снова здравствуйте!", reply_markup=self.generate_keyboard())

    def activate_handlers(self):
        # Start command
        self.updater.dispatcher.add_handler(CommandHandler('start', self.start_command_handler))

        # Check user subscriptions
        self.updater.dispatcher \
            .add_handler(MessageHandler(Filters.text(self.main_keyboard_buttons[0][0]), self.show_user_subscriptions))

        # Writes information on how to subscribe an account
        self.updater.dispatcher \
            .add_handler(MessageHandler(Filters.text(self.main_keyboard_buttons[0][1]), self.write_subscription_guide))

        # Subscribe an account
        self.updater.dispatcher \
            .add_handler(
                MessageHandler(
                    Filters.regex(r'(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am|instagr.com)\/(\w+)'),
                    self.subscribe_user
                )
            )

        # Unknown command
        self.updater.dispatcher \
            .add_handler(MessageHandler(Filters.all, self.write_unknown_command_exception))

    def generate_keyboard(self):
        return ReplyKeyboardMarkup(self.main_keyboard_buttons,
                                   one_time_keyboard=False,
                                   resize_keyboard=True)

    def write_unknown_command_exception(self, update: Update, context: CallbackContext):
        update.message.reply_text('Неизвестная команда ¯\\_(ツ)_/¯', reply_markup=self.generate_keyboard())

    def show_user_subscriptions(self, update: Update, context: CallbackContext):
        update.message.reply_text('TBA', reply_markup=self.generate_keyboard())

    def write_subscription_guide(self, update: Update, context: CallbackContext):
        update.message.reply_text('Пришлите ссылку на инстаграм аккаунт 🥺')

    def subscribe_user(self, update: Update, context: CallbackContext):
        blogger_short_name = re.match\
            (r'(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am|instagr.com)\/(\w+)', update.message.text)\
            .group(1)

        self.controller.subscribe_user(update.message.from_user.id, blogger_short_name)
        update.message.reply_text('Пока не реализовано', reply_markup=self.generate_keyboard())
