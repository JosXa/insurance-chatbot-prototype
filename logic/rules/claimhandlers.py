import random
import re
from pprint import pprint

from core import Context, States, ChatAction
from core.dialogmanager import ForceReevaluation
from logic.rules import answercheckers
from logic.rules.smalltalkhandlers import change_topic
from logic.sentencecomposer import SentenceComposer
from model import UserAnswers
from logzero import logger as log


def chance(value: float) -> bool:
    return random.random() < value


def start(r, c: Context):
    # TODO: If user has already interacted (after bot restart), go immediately to "current" question
    if c.last_user_utterance.intent == 'smalltalk.greetings.whatsup':
        r.say("smalltalk.greetings.whatsup")
        return
    r.say("hello")
    if not c.has_outgoing_intent('how are you', 10):
        r.ask("how are you")
        return 'asking', 'how_are_you', 1
    else:
        if not c.has_outgoing_intent('what i can do', 10):
            r.say("what i can do")
        else:
            r.say("what you can say")
        return States.SMALLTALK


def intro(r, c):
    if not c.has_outgoing_intent("what i can do", age_limit=10):
        r.say("what i can do")
    r.say("what you can say")
    return "explained_something", 1


def ask_to_start(r, c):
    if c.get_value('user_no_claim', False):
        return
    else:
        r.ask("claim damage", choices=['affirm_yes', 'negate_no'])
    return 'ask_to_start', 2


def record_phone_damage(r, c: Context):
    if c.current_question.id in ('damage_type', 'cause_of_damage'):
        return  # We handle this as a normal answerchecker

    dmg_type = c.last_user_utterance.parameters.get('damage_type')
    dmg_type = dmg_type[0] if isinstance(dmg_type, list) and len(dmg_type) > 0 else dmg_type
    if dmg_type:
        c.add_answer_to_question('damage_type', str(dmg_type))

    if not c.has_outgoing_intent("sorry for broken phone", 40):
        r.say("sorry for broken phone")  # Automatically grounds damage_type if given

    c.set_value('is_phone_broken', True)
    return True


def start_claim(r, c):
    c.set_value("claim_started", True)
    r.say("start claim").then_ask(c.current_question, delay=ChatAction.Delay.VERY_LONG)
    return States.ASKING_QUESTION


def user_no_claim(r, c: Context):
    c.set_value('user_no_claim', True)
    r.say('pity_no_claim', 'chat on')
    return States.SMALLTALK


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
    if callable(specific_answer_matcher):
        result = specific_answer_matcher(r, c, question)
        if isinstance(result, (list, tuple)):  # Multiple results found
            r.ask('please select choice', choices=result)
        elif result is False:  # Invalid answer by user
            r.say('sorry', 'invalid answer').give_hint(question)
        elif result is None:
            return  # Actions already handled in answer matcher
        else:
            if question.confirm:
                return ask_to_confirm_answer(r, c, user_answer=result)
            else:
                return store_answer(r, c, user_answer=result)
        return

    ut = c.last_user_utterance

    if question.media:
        if ut.media_location:
            # No confirmation required
            return store_answer(r, c, user_answer=ut.media_location)
        else:
            r.say('please send media')
            return States.ASKING_QUESTION
    if ut.media_location:
        r.say('sorry', 'invalid answer').give_hint(question)
        return States.ASKING_QUESTION

    if question.is_valid(ut.text):
        if question.confirm:
            return ask_to_confirm_answer(r, c, user_answer=ut.text)
        else:
            return store_answer(r, c, user_answer=ut.text)
    else:
        r.say('sorry', 'invalid answer').give_hint(question)
        return States.ASKING_QUESTION


def store_answer(r, c, question=None, user_answer=None):
    # Assumes answer is checked for validity
    if not user_answer:
        user_answer = c.get_value('user_answer')
    if not question:
        question = c.current_question

    c.add_answer_to_question(question, user_answer)

    if question.implicit_grounding:
        r.implicitly_ground(question, user_answer)
    else:
        r.say("ok thank you")
    return ask_next_question(r, c)


def ask_to_confirm_answer(r, c, user_answer=None):
    if user_answer is None:
        user_answer = c.last_user_utterance.text
    r.ask_to_confirm(c.current_question, user_answer)
    c.set_value('user_answer', user_answer)
    return 'user_confirming_answer', 1


def ask_next_question(r: SentenceComposer, c):
    if c.claim_finished:
        return claim_finished(r, c)

    while not c.current_question.is_applicable(r.loader.selection_context):
        c.add_answer_to_question(c.current_question, UserAnswers.NO_ANSWER)

    if c.current_questionnaire.is_first_question(c.current_question):
        # started a new questionnaire
        if c.has_answered_questions:
            r.say("questionnaire finished")
        if not c.current_question.id == 'cause_of_damage':
            r.send_title(c.current_questionnaire)

    r.then_ask(c.current_question)
    return States.ASKING_QUESTION


def repeat_question(r, c):
    r.say("again").ask(c.current_question)
    return States.ASKING_QUESTION


def skip_question(r, c):
    if c.current_question.is_required:
        r.say("sorry", "but", "cannot skip this question")
        r.ask("continue anyway", choices=("affirm_yes", "negate_no"))
        return "ask_continue_despite_no_skipping", 1
    else:
        if not c.current_question.id == 'remarks':
            r.say("skip this question", parameters={'question': c.current_question})

        c.add_answer_to_question(c.current_question, UserAnswers.NO_ANSWER)
        return ask_next_question(r, c)


def excuse_did_not_understand(r, c):
    r.say("sorry", "but", "did not understand")
    if chance(0.8) and c.questionnaire_completion_ratio > 0.3:
        r.say("reformulate")


def abort_claim(r, c):
    r.say("claim aborted")


def claim_finished(r, c):
    r.say('claim finished')
    return preview_claim(r, c)


def preview_claim(r, c):
    all_answers = UserAnswers.get_name_answer_dict(c.user)
    r.ask(
        "preview claim",
        parameters=dict(answers=all_answers),
        choices=['affirm_submit', 'negate_no']
    )
    return "previewing_claim"


def submit_claim(r, c):
    c.set_value('claim_started', False)
    r.say("evaluate prototype")
    return States.SMALLTALK


def claim_needs_editing(r, c):
    print("claim needs editing!")


def user_astonished(r, c):
    r.say("i think so too", "scope of bot")


def change_formal_address(r, c: Context):
    if c.get_value("we_say_du"):
        r.say("we say du")
        c.set_value("we_say_du", False)
        return

    ut = c.last_user_utterance
    if not ut.text:
        return

    # If the formal address changes, we need to force a reevaluation of the response templates parameters,
    # so that the changes go into effect
    if re.search(r'\b(du|dein|dich|dir)\b', ut.text, re.IGNORECASE):
        if c.user.formal_address is True:
            c.user.formal_address = False
            c.set_value("we_say_du", True)
            c.user.save()
            raise ForceReevaluation
    elif re.search(r'\b([Ii]hr|Sie|Ihnen|Euer|haben [sS]ie|sind [Ss]ie)\b', ut.text):
        if c.user.formal_address is False:
            c.user.formal_address = True
            c.user.save()
            raise ForceReevaluation


def no_rule_found(r, c):
    # TODO: This is debatable. Should the user always be notified that something was not understood?
    r.say("sorry", "what i understood", parameters={'understanding': c.last_user_utterance.intent})
    if c.get_value('claim_started', False):
        return
    if chance(0.6):
        return change_topic(r, c)
    else:
        r.say("ask something else")
