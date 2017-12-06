from pprint import pprint
from threading import Thread

from flask import logging, Flask, request
from telegram import Bot
from telegram.ext import Updater, Filters, MessageHandler
from typing import Callable

from clients.botapiclients import IBotAPIClient

log = logging.getLogger(__name__)


class TelegramClient(IBotAPIClient):
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
        data = request.get_data(as_text=True)
        pprint(data)
        self.updater.update_queue.put(data)

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
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, callback))

    def send_message(self, recipient_id, text):
        self.bot.send_message(recipient_id, text)
