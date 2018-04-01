import os

from telegram import Bot

from clients.supportchannel import SupportChannel


class TelegramSupportChannel(SupportChannel):
    """
    Concrete implementation of a `SupportChannel`.

    Sends notifications and files to an actual Telegram "Channel" (the name is ambiguous).
    """

    def __init__(self, telegram_bot: Bot, channel_id):
        self.channel_id = channel_id
        self.bot = telegram_bot

    def send_file(self, filepath, caption=None, filename=None):
        filename = filename or os.path.split(filepath)[-1]
        return self.bot.send_document(
            self.channel_id,
            open(filepath, 'rb'),
            filename=filename,
            caption=caption,
            disable_notification=True,
            timeout=120  # We always want to get these
        )

    def send_notification(self, text):
        return self.bot.send_message(
            self.channel_id,
            text,
            disable_web_page_preview=True,
            disable_notification=False,
            timeout=120  # We always want to get these
        )
