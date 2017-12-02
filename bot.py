from signal import signal, SIGTERM
from threading import Thread
from time import sleep

from telegram import Bot, Update
from typing import List

import settings
from clients.facebook import FacebookClient
from clients.telegram import TelegramClient

threads = list()  # type: List[Thread]


def test_handler(bot: Bot, update: Update):
    update.effective_message.reply_text(update.message.text)


def stop_threads():
    # TODO
    for t in threads:
        pass


def main():
    fb = FacebookClient(
        settings.FACEBOOK_ACCESS_TOKEN
    )
    fb.initialize()

    tg = TelegramClient(
        settings.TELEGRAM_ACCESS_TOKEN,
        settings.TELEGRAM_WEBHOOK_URL,
        settings.TELEGRAM_WEBHOOK_PORT,
        worker_count=4
    )
    tg.initialize()

    tg.add_plaintext_handler(test_handler)

    fb.start_listening()
    tg.start_listening()

    signal(SIGTERM, stop_threads())
    while True:
        sleep(1)


if __name__ == '__main__':
    main()
