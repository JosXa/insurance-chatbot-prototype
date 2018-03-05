import datetime
import itertools
import os
import sched
import threading
import time
from typing import List

from logzero import logger as log
from ruamel.yaml.comments import CommentedMap

import utils
from core import ChatAction
from model import Update

# class IConversationRecorder(ABCMeta):
#     def record_dialog(self, update: Update, actions: List[ChatAction]) -> NoReturn: pass


PATH = 'tests/recordings'
if not os.path.exists(PATH):
    os.makedirs(PATH)


class ConversationRecorder:
    # Time of inactivity, where the user does not say anything. When the duration has passed, publish the generated
    # conversation.yml to a support channel.
    # CLOSING_TIMEFRAME = datetime.timedelta(minutes=5)
    CLOSING_TIMEFRAME = datetime.timedelta(minutes=5)

    def __init__(self, telegram_bot, support_channel_id):
        self.bot = telegram_bot
        self.support_channel_id = support_channel_id
        self.conversations = {}

        self.date_started = datetime.datetime.now()
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._wait_publish_events = {}

    def record_dialog(self, update: Update, actions: List[ChatAction]):
        entry = CommentedMap(
            user_says=update.message_text,
            intent=update.understanding.intent,
            parameters=update.understanding.parameters,
            responses=list(itertools.chain.from_iterable([a.intents for a in actions]))
        )
        self.conversations.setdefault(update.user.id, []).append(entry)
        self._save(update.user.id, schedule_publish=True)

    def _close_and_publish(self, user_id):
        self.bot.send_document(
            self.support_channel_id,
            open(self._get_filepath(user_id), 'rb'),
            caption=self._get_filename(user_id),
            disable_notification=True
        )
        log.info(f"Published conversation recording for {user_id}.")
        del self.conversations[user_id]

    def _get_filename(self, user_id):
        return f"{user_id}_{self.date_started.strftime('%Y%m%d-%H%M%S')}.yml"

    def _get_filepath(self, user_id):
        return os.path.join(PATH, self._get_filename(user_id))

    def _save(self, user_id, schedule_publish=True):
        utils.save_dict_as_yaml(self._get_filepath(user_id), self.conversations[user_id])

        if not schedule_publish:
            return
        if self._wait_publish_events.get(user_id, None):
            try:
                self._scheduler.cancel(self._wait_publish_events[user_id])
            except ValueError:
                pass  # Happens if we're too fast for some reason
        self._wait_publish_events[user_id] = self._scheduler.enter(
            int(self.CLOSING_TIMEFRAME.total_seconds()),
            1,
            action=self._close_and_publish,
            argument=(user_id,)
        )
        threading.Thread(target=self._scheduler.run).start()
