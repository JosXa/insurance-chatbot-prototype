import datetime
import itertools
import unittest
import warnings
from typing import List

import settings
import util
from clients.nluclients import DialogflowClient
from core import ChatAction, ContextManager, States
from logic.planning import PlanningAgent
from logic.rules.dialogcontroller import application_router
from model import Update, User


# TODO: Migrate to py.test
class RuleTests:
    def __init__(self):
        self.router = application_router
        self.nlp = DialogflowClient(settings.DIALOGFLOW_ACCESS_TOKEN)
        self.context_manager = ContextManager(States.SMALLTALK)
        self.planning_agent = PlanningAgent(self.router)
        self.msg_count = 0
        self.conversation = util.load_yaml_as_dict('conversation.yml')
        self.user = User(insurance_id=1234)
        self.user.save()

    def say(self, text):
        update = Update()
        update.message_text = text
        update.message_id = self.msg_count
        update.datetime = datetime.datetime.now()
        update.user = self.user

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.nlp.insert_understanding(update)
        context = self.context_manager.add_incoming_update(update)

        next_response = self.planning_agent.build_next_actions(context)

        actions = next_response.collect_actions()

        context.add_actions(actions)

        self.msg_count += 1
        return actions

    def assertIntentsEqual(self, collection: List[ChatAction], search, message: str = None):
        if isinstance(search, str):
            search = [search]
        if not isinstance(search, list):
            search = list(search)
        found_intents = list(itertools.chain.from_iterable([c.intents for c in collection]))
        assert found_intents == search, message

    def test_full_conversation(self):
        for dialog in self.conversation:
            user_says = dialog.get('user_says')
            user_intent = dialog.get('intent')
            expected_responses = dialog.get('responses')
            self.assertIntentsEqual(self.say(user_says), expected_responses)


if __name__ == '__main__':
    unittest.main()
