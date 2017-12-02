from flask import logging
from telegram.ext import Updater

from clients.botapiclients import IBotAPIClient

log = logging.getLogger(__name__)


class TelegramClient(IBotAPIClient):
    def __init__(self, token, webhook_url, webhook_port, worker_count):
        self.token = token
        self.webhook_url = webhook_url
        self.webhook_port = webhook_port
        self.worker_count = worker_count

        self.updater = None

    def initialize(self):
        self.updater = Updater(token=self.token)

    def start_listening(self):
        self.updater.start_webhook(listen="0.0.0.0",
                                   port=self.webhook_port,
                                   url_path=self.token)
        self.updater.bot.set_webhook(self.webhook_url + self.token)
        self.updater.idle()

    def connect(self):
        pass

    def send_message(self):
        pass
