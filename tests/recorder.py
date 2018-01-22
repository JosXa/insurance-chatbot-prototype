import datetime
import itertools
import os
import time
from collections import OrderedDict
from typing import List

import ruamel

from ruamel.yaml.comments import CommentedMap

import utils
from logic import ChatAction
from model import Update, User

PATH = 'tests/recordings'
if not os.path.exists(PATH):
    os.makedirs(PATH)


class ConversationRecorder(object):
    def __init__(self, for_user: User):
        self.user = for_user
        self.conversation = []
        self.date_started = datetime.datetime.now()

    def record_dialog(self, update: Update, actions: List[ChatAction]):
        if update.user != self.user:
            return

        entry = CommentedMap(
            user_says=update.message_text,
            intent=update.understanding.intent,
            parameters=update.understanding.parameters,
            responses=list(itertools.chain.from_iterable([a.intents for a in actions]))
        )
        self.conversation.append(entry)

    def save(self):
        filename = f"{self.user.id}_{self.date_started.strftime('%Y%m%d-%H%M%S')}.yml"
        filepath = os.path.join(PATH, filename)
        utils.save_dict_as_yaml(filepath, self.conversation)
