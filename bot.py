from signal import signal, SIGTERM
from threading import Thread

from telegram import Bot, Update
from typing import List

import settings
from clients.facebook import FacebookClient
from clients.telegram import TelegramClient

threads = list()  # type: List[Thread]

def test_handler(bot: Bot, update: Update):
    update.effective_message.reply_text(update.message.text)

def stop_threads():
    for t in threads:
        t.join()

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

    threads.append(fb.start_listening())
    threads.append(tg.start_listening())

    signal(SIGTERM, stop_threads())




if __name__ == '__main__':
    main()
