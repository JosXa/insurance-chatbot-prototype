from pprint import pprint

from flask import logging, Flask, request
from telegram import Bot
from telegram.ext import Updater, Filters, MessageHandler
from typing import Callable

from clients.botapiclients import IBotAPIClient

log = logging.getLogger(__name__)


class TelegramClient(IBotAPIClient):
    def __init__(self, app: Flask, webhook_url, token, worker_count):
        self._webhook_url = webhook_url
        self._app = app
        self._token = token
        self._worker_count = worker_count

        self.updater = None  # type: Updater
        self.bot = None  #type: Bot
        self._running = False

    def initialize(self):
        self.updater = Updater(token=self._token)
        self.bot = self.updater.bot

    def add_plaintext_handler(self, callback: Callable):
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, callback))

    def _webhook_endpoint(self):
        data = request.get_data(as_text=True)
        pprint(data)
        self.updater.update_queue.put(data)

    def start_listening(self):
        self.updater.job_queue.start()
        self.bot.set_webhook(self._webhook_url + self._token)
        self._app.add_url_rule(self._token, view_func=self._webhook_endpoint)

    def stop_listening(self):
        self.updater.stop()

    def connect(self):
        pass

    def send_message(self, recipient_id, text):
        self.bot.send_message(recipient_id, text)
