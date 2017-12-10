from threading import Thread
from typing import Callable

from flask import logging, Flask, request
from telegram import Bot, Update as TelegramUpdate
from telegram.ext import Updater, Filters, MessageHandler

from clients.botapiclients import IBotAPIClient
from clients.common.update import Update
from model import User

log = logging.getLogger(__name__)


class TelegramClient(IBotAPIClient):
    def unify_update(self, update: TelegramUpdate):
        ud = Update()
        ud.original_update = update
        ud.client_name = self.client_name

        ud.user, created = User.get_or_create(telegram_id=update.effective_user.id)
        if created:
            ud.user.save()
        ud.message_text = update.effective_message.text
        return ud

    @property
    def client_name(self):
        return 'telegram'

    def __init__(self, app: Flask, webhook_url, token):
        self._webhook_url = webhook_url
        self._app = app
        self._token = token

        self.updater = None  # type: Updater
        self.bot = None  # type: Bot
        self._running = False
        self.__threads = list()

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
        self.updater.dispatcher.add_handler(MessageHandler(
            Filters.text, lambda bot, update: callback(update)))

    def send_message(self, recipient: User, text):
        self.bot.send_message(recipient.telegram_id, text)

    def add_error_handler(self, callback: Callable):
        self.updater.dispatcher.add_error_handler(callback)
