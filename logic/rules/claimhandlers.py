import random
import re

from logzero import logger

from core import Context, States
from logic.rules import answercheckers
from model import UserAnswers
from logzero import logger as log


def chance(value: float) -> bool:
    return random.random() < value


def start(r, c: Context):
    # TODO: If user has already interacted (after bot restart), go immediately to "current" question
    r.say("hello")
    if not c.has_outgoing_intent('how are you', 10):
        r.ask("how are you")
        return 'asking', 'how_are_you', 1
    return 'smalltalk'


def intro(r, c):
    if not c.has_outgoing_intent("what i can do", age_limit=10):
        r.say("what i can do")
    r.say("what you can say")


def ask_to_start(r, c):
    r.ask("claim damage", choices=['affirm_yes', 'negate_no'])
    return 'ask_to_start'


def record_phone_damage(r, c: Context):
    r.say("sorry for that")
    dmg_type = c.last_user_utterance.parameters.get('damage_type')
    if dmg_type:
        c.add_answer_to_question('damage_type', str(dmg_type))
    c.set_value('is_phone_broken', True)


def begin_questionnaire(r, c):
    r.say("with pleasure").then_ask(c.current_question)
    return States.ASKING_QUESTION


def user_no_claim(r, c: Context):
    c.set_value('user_no_claim', True)
    r.say('pity_no_claim', 'chat on')
    return 'smalltalk'


def send_example(r, c):
    r.give_example(c.current_question)


def clarify(r, c: Context):
    should_send_example = False
    if c.last_user_utterance.intent == 'example':
        should_send_example = True

    if c.has_outgoing_intent('give_hint', age_limit=2):
        should_send_example = True
    else:
        r.give_hint(c.current_question)

    if should_send_example:
        send_example(r, c)


def check_answer(r, c):
    question = c.current_question

    # There are specific implementations of matchers that have a special functionality (e.g. getting phone model)
    specific_answer_matcher = getattr(answercheckers, question.id, None)
    if specific_answer_matcher:
        return specific_answer_matcher(r, c)

    if question.is_valid(c.last_user_utterance.text):
        if question.confirm:
            return ask_to_confirm_answer(r, c)
        else:
            return store_answer(r, c, user_answer=c.last_user_utterance.text)
    else:
        r.say('sorry', 'invalid answer').give_hint(question)
        return States.ASKING_QUESTION


def store_answer(r, c, user_answer=None):
    # Assumes answer is checked for validity
    if not user_answer:
        user_answer = c.get_value('user_answer')
    c.add_answer_to_question(c.current_question, user_answer)
    r.say("ok thank you")
    return ask_next_question(r, c)


def ask_to_confirm_answer(r, c):
    r.ask_to_confirm(c.current_question, c.last_user_utterance.text)
    c.set_value('user_answer', c.last_user_utterance)
    return 'user_confirming_answer'


def ask_next_question(r, c):
    if c.current_questionnaire.is_first_question(c.current_question):
        # started a new questionnaire
        if c.has_answered_questions:
            r.say("questionnaire finished")

    r.then_ask(c.current_question)
    return States.ASKING_QUESTION


def repeat_question(r, c):
    r.say("again").ask(c.current_question)
    return States.ASKING_QUESTION


def skip_question(r, c):
    if c.current_question.is_required:
        r.say("sorry", "but", "cannot skip this question")
        r.ask("continue anyway", choices=("affirm_yes", "negate_no"))
        return "ask_continue_despite_no_skipping"
    else:
        r.say("skip this question", parameters={'question': c.current_question})
        c.add_answer_to_question(c.current_question, UserAnswers.NO_ANSWER)
        ask_next_question(r, c)


def excuse_did_not_understand(r, c):
    r.say("sorry", "but", "did not understand")
    if chance(0.8) and c.questionnaire_completion_ratio > 0.3:
        r.say("reformulate")


def abort_claim(r, c):
    print("CLAIM ABORTED")  # TODO


def user_astonished(r, c):
    r.say("i think so too", "scope of bot")


def change_formal_address(r, c: Context):
    def switch_to_du():
        c.user.formal_address = False
        # r.say("we say du")
        c.user.save()

    ut = c.last_user_utterance

    if re.search(r'\b(du|dein|dich|dir)\b', ut.text, re.IGNORECASE):
        if c.user.formal_address is True:
            switch_to_du()
    elif re.search(r'\b([Ii]hr|Sie|Ihnen|Euer|haben [sS]ie|sind [Ss]ie)\b', ut.text):
        c.user.formal_address = True
        c.user.save()


def no_rule_found(r, c):
    r.say("sorry", "what i understood", parameters={'understanding': c.last_user_utterance.intent})
    if chance(0.5):
        r.say("ask something else")
