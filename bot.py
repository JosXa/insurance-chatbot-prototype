from pprint import pprint
from signal import signal, SIGTERM
from threading import Thread
from time import sleep

from telegram import Bot, Update
from typing import List

import settings
from clients.facebook import FacebookClient
from clients.telegram import TelegramClient

threads = list()  # type: List[Thread]

USER_SEQ = dict()


def test_handler_tg(bot: Bot, update: Update):
    update.effective_message.reply_text(update.message.text)


def test_handler_fb(page, event):
    sender_id = event.sender_id
    recipient_id = event.recipient_id
    time_of_message = event.timestamp
    message = event.message

    seq = message.get("seq", 0)
    message_id = message.get("mid")
    app_id = message.get("app_id")
    metadata = message.get("metadata")

    message_text = message.get("text")
    message_attachments = message.get("attachments")
    quick_reply = message.get("quick_reply")

    seq_id = sender_id + ':' + recipient_id
    if USER_SEQ.get(seq_id, -1) >= seq:
        print("Ignore duplicated request")
        return None
    else:
        USER_SEQ[seq_id] = seq

    if quick_reply:
        quick_reply_payload = quick_reply.get('payload')
        print("quick reply for message %s with payload %s" % (message_id, quick_reply_payload))

        page.send(sender_id, "Quick reply tapped")

    if message_text:
        page.send_message(sender_id, message_text)
    elif message_attachments:
        page.send(sender_id, "Message with attachment received")


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

    tg.add_plaintext_handler(test_handler_tg)
    fb.add_plaintext_handler(test_handler_fb)

    fb.start_listening()
    tg.start_listening()

    signal(SIGTERM, stop_threads())
    while True:
        sleep(1)


if __name__ == '__main__':
    main()
