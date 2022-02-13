from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters


class Telegram:
    def __init__(self, token):
        self.updater = Updater(token)

        self.main_keyboard_buttons = [['Мои подписки', 'Подписаться']]

        self.activate_handlers()

        self.updater.start_polling()
        self.updater.idle()

    def message_handler(self, update: Update, context: CallbackContext) -> None:
        print(update)
        print(update.message.text)
        if update.message.text == 'Ку':
            update.message.reply_text(f'Hello {update.effective_user.first_name}')
        else:
            self.activate_keyboard(update, context)

    def activate_handlers(self):
        self.updater.dispatcher.add_handler(CommandHandler('start', self.activate_keyboard))

        self.updater.dispatcher\
            .add_handler(MessageHandler(Filters.text(self.main_keyboard_buttons[0][0]), self.show_user_subscriptions))

        self.updater.dispatcher\
            .add_handler(MessageHandler(Filters.text(self.main_keyboard_buttons[0][1]), self.subscribe_user))

    def activate_keyboard(self, update: Update, context: CallbackContext):
        reply_markup = ReplyKeyboardMarkup(self.main_keyboard_buttons,
                                           one_time_keyboard=False,
                                           resize_keyboard=True)

        update.message.reply_text("Здравствуйте!", reply_markup=reply_markup)

    def show_user_subscriptions(self, update: Update, context: CallbackContext):
        update.message.reply_text('TBA')

    def subscribe_user(self, update: Update, context: CallbackContext):
        reply_markup = ReplyKeyboardRemove()

        update.message.reply_text('Пришлите ссылку на инстаграм аккаунт', reply_markup=reply_markup)
