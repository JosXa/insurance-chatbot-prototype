import time
from threading import Thread
from typing import Callable, List

from flask import Flask, logging, request
from telegram import *
from telegram import ChatAction as TelegramChatAction, Update as TelegramUpdate
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

import utils
from clients.botapiclients import IBotAPIClient
from logic import ChatAction
from model import User
from model.update import Update

log = logging.getLogger(__name__)


class TelegramClient(IBotAPIClient):
    def __init__(self, app: Flask, webhook_url, token, test_mode=False):
        self._webhook_url = webhook_url
        self._app = app
        self._token = token

        self.updater = None  # type: Updater
        self.bot = None  # type: Bot
        self._test_mode = test_mode
        self._running = False
        self.__threads = list()

    def unify_update(self, update: TelegramUpdate):
        ud = Update()
        ud.original_update = update
        ud.client_name = self.client_name

        ud.user, created = User.get_or_create(telegram_id=update.effective_user.id)
        if created:
            ud.user.save()
        ud.message_id = update.effective_message.message_id
        ud.message_text = update.effective_message.text
        ud.datetime = update.effective_message.date
        ud.save()
        return ud

    def perform_actions(self, actions: List[ChatAction]):

        for action in actions:
            chat_id = action.peer.telegram_id

            if action.show_typing:
                self.bot.send_chat_action(chat_id, TelegramChatAction.TYPING)
            if action.delay:
                time.sleep(action.delay.value)

            markup = None
            if action.action_type == ChatAction.Type.ASKING_QUESTION:
                if action.choices:
                    buttons = [KeyboardButton(x) for x in action.choices]
                    markup = ReplyKeyboardMarkup(utils.build_menu(buttons, 3),
                                                 resize_keyboard=True,
                                                 one_time_keyboard=True,
                                                 selective=True)
                else:
                    markup = ForceReply()

            self._send_message(peer=action.peer, text=action.render(), markup=markup)

    @property
    def client_name(self):
        return 'telegram'

    def _init_thread(self, target, *args, **kwargs):
        thr = Thread(target=target, args=args, kwargs=kwargs)
        thr.start()
        self.__threads.append(thr)

    def initialize(self):
        self.updater = Updater(token=self._token)
        self.bot = self.updater.bot

    def _webhook_endpoint(self):
        data = request.get_json()
        update = TelegramUpdate.de_json(data, self.updater.bot)
        self.updater.update_queue.put(update)

        return 'OK'

    def start_listening(self):
        # Start ptb threads
        self.updater.job_queue.start()
        self._init_thread(self.updater.dispatcher.start)

        if self._test_mode:
            self.updater.start_polling()
            return

        # Construct URL and set webhook
        url = self._webhook_url + self._token
        self.bot.set_webhook(url)
        self._app.add_url_rule(f"/{self._token}",
                               view_func=self._webhook_endpoint,
                               methods=['POST', 'GET'])

    def stop_listening(self):
        self.updater.job_queue.stop()
        self.updater.dispatcher.stop()
        self.updater.stop()

    def add_plaintext_handler(self, callback: Callable):
        self.updater.dispatcher.add_handler(
            MessageHandler(
                Filters.text,
                lambda bot, update: callback(self, self.unify_update(update))
            ))

    def set_start_handler(self, callback: Callable):
        self.updater.dispatcher.add_handler(
            CommandHandler(
                "start",
                lambda bot, update: callback(self, self.unify_update(update))
            ))

    def _send_message(self, peer: User, text: str, markup=None):
        """
        Sends a markdown-formatted message to the `recipient`.
        """
        self.bot.send_message(peer.telegram_id, text, parse_mode=ParseMode.HTML,
                              reply_markup=markup)

    def add_error_handler(self, callback: Callable):
        self.updater.dispatcher.add_error_handler(callback)

    def create_reply_keyboard(self, buttons, n_cols=2):
        button_objects = [KeyboardButton(b) for b in buttons]
        # TODO: incorporate util.build_menu
        reply_markup = ReplyKeyboardMarkup(button_objects,
                                           one_time_keyboard=True,
                                           resize_keyboard=True)
        return reply_markup
