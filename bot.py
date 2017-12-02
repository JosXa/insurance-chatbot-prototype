from telegram import Bot, Update

import settings
from clients.facebook import FacebookClient
from clients.telegram import TelegramClient


def test_handler(bot: Bot, update: Update):
    update.effective_message.reply_text(update.message.text)


def main():
    tg = TelegramClient(
        settings.TELEGRAM_ACCESS_TOKEN,
        settings.TELEGRAM_WEBHOOK_URL,
        settings.TELEGRAM_WEBHOOK_PORT,
        worker_count=4
    )
    tg.initialize()

    tg.add_plaintext_handler(test_handler)

    tg.start_listening()

    fb = FacebookClient(
        settings.FACEBOOK_ACCESS_TOKEN
    )
    fb.initialize()
    fb.start_listening()


if __name__ == '__main__':
    main()
