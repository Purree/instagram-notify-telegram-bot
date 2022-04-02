import asyncio
import re
import threading

import aiohttp
import numpy as np
import telegram
from telegram import Update, ReplyKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

from Config import Config
from Debug import Debug
from InstagramHandler import InstagramHandler
from UserController import UserController


class Telegram:
    def __init__(self, token):
        self.debug = Debug()
        self.updater = Updater(token)
        self.bot = telegram.Bot(token)
        self.controller = UserController()

        self.main_keyboard_buttons = [['Мои подписки', 'Подписаться'], ['Мои тарифы', 'Отписаться']]

        self.activate_handlers()
        self.updater.start_polling()

        # Initialize new posts handler
        InstagramHandler(Config().get_all_section_parameters("INSTAGRAM"), self)

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
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

        # Check user tariffs
        self.updater.dispatcher \
            .add_handler(MessageHandler(Filters.text(self.main_keyboard_buttons[1][0]), self.show_user_tariffs))

        # Writes information on how to unsubscribe an account
        self.updater.dispatcher \
            .add_handler(
            MessageHandler(Filters.text(self.main_keyboard_buttons[1][1]), self.write_unsubscription_guide))

        # Unsubscribe from account
        self.updater.dispatcher \
            .add_handler(CommandHandler('unsub', self.unsubscribe_user))

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

    def show_user_tariffs(self, update: Update, context: CallbackContext):
        user_tariffs = self.controller.get_user_tariffs(update.message.from_user.id)
        tariffs_list = ""

        for tariff in user_tariffs:
            tariffs_list += tariff[7] + f" {tariff[8] or ''}" + "\n"

        update.message.reply_text('Список ваших тарифов:\n' + tariffs_list,
                                  reply_markup=self.generate_keyboard(),
                                  )

    def show_user_subscriptions(self, update: Update, context: CallbackContext):
        user_subscriptions = self.controller.get_user_subscriptions(update.message.from_user.id)
        subscriptions_list = ""

        for subscription in user_subscriptions:
            subscriptions_list += subscription[2] + f" ({subscription[1]})" + "\n"

        update.message.reply_text('Список ваших подписок:\n' +
                                  subscriptions_list +
                                  "Чтобы отписаться напишите /unsub + цифры в скобочках"
                                  if subscriptions_list != "" else
                                  "У вас нет подписок",
                                  reply_markup=self.generate_keyboard(),
                                  )

    def unsubscribe_user(self, update: Update, context: CallbackContext):
        try:
            blogger_id = re.findall(r'\d+', update.message.text)[0]
        except IndexError as error:
            self.send_error_message(update, "Введены невалидные данные")
            return

        unsubscribe_result = self.controller.unsubscribe_user(update.message.from_user.id, blogger_id)
        if unsubscribe_result.isSuccess:
            update.message.reply_text('Вы успешно отписались от этого пользователя',
                                      reply_markup=self.generate_keyboard(),
                                      )
            return

        self.send_error_message(update, unsubscribe_result.errorMessage)

    def write_subscription_guide(self, update: Update, context: CallbackContext):
        update.message.reply_text('Пришлите ссылку на инстаграм аккаунт 🥺')

    def write_unsubscription_guide(self, update: Update, context: CallbackContext):
        update.message.reply_text('Выполните команду /unsub + цифры из скобочек из раздела ' +
                                  self.main_keyboard_buttons[0][0])

    def subscribe_user(self, update: Update, context: CallbackContext):
        threading.Thread(target=self._subscribe_user, args=([update, context])).start()

    def _subscribe_user(self, update: Update, context: CallbackContext):
        blogger_short_name = \
            re.match(r'(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am|instagr.com)\/(\w+)',
                     update.message.text).group(1)

        user_subscription = self.controller.subscribe_user(update.message.from_user.id, blogger_short_name)

        if not user_subscription.isSuccess:
            self.send_error_message(update, user_subscription.errorMessage)
        else:
            update.message.reply_text('Вы успешно подписаны на ' + user_subscription.returnValue,
                                      reply_markup=self.generate_keyboard())

    def send_error_message(self, update, error_text):
        update.message.reply_text(error_text, reply_markup=self.generate_keyboard())

    def send_new_posts_message(self, blogger_with_subscribers):
        receivers_ids = [blogger_data[4] for blogger_data in blogger_with_subscribers]
        blogger_short_name = blogger_with_subscribers[0][1]

        self.debug.dump(receivers_ids, "получили сообщения о новом посте у", blogger_short_name)

        return asyncio.run(
            self._send_message_to_many_users("У пользователя %s новый пост" % blogger_short_name, receivers_ids))

    def send_new_stories_message(self, blogger_with_subscribers):
        receivers_ids = [blogger_data[4] for blogger_data in blogger_with_subscribers]
        blogger_short_name = blogger_with_subscribers[0][1]

        self.debug.dump(receivers_ids, "получили сообщения о новой сторис у", blogger_short_name)

        return asyncio.run(
            self._send_message_to_many_users("У пользователя %s новая сторис" % blogger_short_name, receivers_ids))

    def send_custom_message(self, message_text, receiver_id):
        asyncio.run(self._send_message_to_user_async(message_text, receiver_id))

    async def _send_message_to_many_users(self, message_text: str, receivers_ids: list):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for receiver_id in receivers_ids:
                tasks.append(asyncio.ensure_future(self._send_message_to_user_async(message_text, receiver_id)))

            return await asyncio.gather(*tasks)

    async def _send_message_to_user_async(self, message_text, receiver_id):
        self.debug.dump(message_text, receiver_id)
        return self.bot.sendMessage(text=message_text, chat_id=receiver_id)

    def send_medias(self, medias_data, chat_ids: list, reply_to=None):
        threading.Thread(target=self._send_medias_thread, args=([medias_data, chat_ids, reply_to])).start()

    def _send_medias_thread(self, medias_data, chat_ids: list, reply_to=None):
        medias = asyncio.run(self._get_medias(medias_data))

        if len(medias) > 10:
            medias_split = self.split_array(medias, 10)
            for media in medias_split:
                asyncio.run(self._send_medias(media, chat_ids, reply_to))
        else:
            asyncio.run(self._send_medias(medias, chat_ids, reply_to))

    async def _send_medias(self, medias, chat_ids: list, reply_to=None):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for chat_id in chat_ids:
                tasks.append(asyncio.ensure_future(self._send_medias_to_user(medias, chat_id, reply_to)))

            return await asyncio.gather(*tasks)

    async def _get_medias(self, medias_data, media_text=None):
        medias = []

        for media in medias_data:
            media = medias_data[media]

            if media['type'] == 'video':
                medias.append(InputMediaVideo(media['url'], media_text or media['text']))

            if media['type'] == 'image':
                medias.append(InputMediaPhoto(media['url'], media_text or media['text']))

            if media['type'] == 'sidecar':
                medias += await self._get_medias(media['attachments'], media['text'])

        return medias

    async def _send_medias_to_user(self, medias, chat_id, reply_to=None):
        try:
            sent_medias = self.bot.send_media_group(chat_id=chat_id, media=medias, reply_to_message_id=reply_to)
        except telegram.error.BadRequest as error:
            self.debug.dump(error)
            return False

        return sent_medias

    def split_array(self, array, chunk_size):
        chunked_list = list()
        for i in range(0, len(array), chunk_size):
            chunked_list.append(array[i:i+chunk_size])

        return chunked_list

