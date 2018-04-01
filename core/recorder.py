import datetime
import itertools
import os
import sched
import threading
import time
from typing import List

from logzero import logger as log
from ruamel.yaml.comments import CommentedMap

import util
from clients.supportchannel import SupportChannel
from core import ChatAction
from core.dialogstates import DialogStates
from model import Update


class ConversationRecorder:
    """
    Records the incoming and outgoing intents of a conversation, as well as internal state changes.
    Produces a YAML file with these sequences of a given conversation.

    With `playconversation.py`, a recording made with this class can be replayed as an "integration test" in real time.
    """

    # Time of inactivity, where the user does not say anything. When the duration has passed, publish the generated
    # conversation.yml to a support channel.
    CLOSING_TIMEFRAME = datetime.timedelta(minutes=3)

    def __init__(self, telegram_bot, support_channel: SupportChannel):
        self.bot = telegram_bot
        self.support_channel = support_channel
        self.conversations = {}

        self.date_started = datetime.datetime.now()
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._wait_publish_events = {}

    def record_dialog(self, update: Update, actions: List[ChatAction], dialog_states: DialogStates):
        entry = CommentedMap(  # ensures ordered key-value pairs
            user_says=update.message_text,
            intent=update.understanding.intent,
            parameters=update.understanding.parameters,
            new_states=[str(x) for x in list(dialog_states.iter_states())],
            responses=list(itertools.chain.from_iterable([a.intents for a in actions]))
        )
        self.conversations.setdefault(update.user.id, []).append(entry)
        self._save(update.user, schedule_publish=True)

    def _close_and_publish(self, user):
        # if settings.DEBUG_MODE:
        #     log.info("Not publishing conversation recording in debug mode.")
        # else:
        try:
            self.support_channel.send_file(
                filepath=self._get_filepath(user),
                caption=str(user)
            )
            log.info(f"Published conversation recording for {user}.")
        except Exception as e:
            log.error(f"Publishing conversation recording failed with error:")
            log.exception(e)
        finally:
            del self.conversations[user.id]

    def _get_filename(self, user):
        return f"{user.id}_{self.date_started.strftime('%Y%m%d-%H%M%S')}.yml"

    def _get_filepath(self, user):
        return os.path.join(user.get_recording_folder(), self._get_filename(user))

    def _save(self, user, schedule_publish=True):
        util.save_dict_as_yaml(self._get_filepath(user), self.conversations[user.id])

        if not schedule_publish:
            return
        if self._wait_publish_events.get(user.id, None):
            try:
                self._scheduler.cancel(self._wait_publish_events[user.id])
            except ValueError:
                pass  # Happens if we're too fast for some reason
        self._wait_publish_events[user.id] = self._scheduler.enter(
            int(self.CLOSING_TIMEFRAME.total_seconds()),
            1,
            action=self._close_and_publish,
            argument=(user,)
        )
        threading.Thread(target=self._scheduler.run).start()
