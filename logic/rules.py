from pprint import pprint

from corpus import get_question_by_id
from logic.chataction import Separator
from logic.context import States, Context
from logic.controller import Controller, IntentHandler


def hello(composer, context):
    # TODO: If user has already interacted (after bot restart), go immediately to "current" question
    composer.say("hello")
    if not context.has_outgoing_intent("what i can do", age_limit=10):
        composer.say("what i can do")
    return States.SMALLTALK


def ask_to_start(composer, context):
    composer.ask("claim damage", choices=['affirm', 'negate'])
    return 'ask_to_start'


def record_phone_damage(composer, context):
    composer.say("sorry for that")
    dmg_type = context.last_user_utterance.parameters.get('damage_type')
    if dmg_type:
        context.add_answer_to_question('damage_type', str(dmg_type))


def clarify(composer, context: Context):
    if context.has_outgoing_intent('give_hint', age_limit=2):
        composer.say('example').concat(context.current_question.example)
    else:
        composer.give_hint(context.current_question)


def check_answer(composer, context):
    question = context.current_question
    if question.is_valid(context.last_user_utterance.text):
        context.add_answer_to_question(question, context.last_user_utterance.text)
        composer.say("ok thank you")
        return ask_next_question(composer, context)
    else:
        composer.say('sorry', 'invalid answer').give_hint(question)
        return States.ASKING_QUESTION


def begin_questionnaire(composer, context):
    composer.say("with pleasure").then_ask(context.current_question)
    return States.ASKING_QUESTION


def user_no_claim(composer, context):
    print("user has no claim to make")  # TODO


def ask_next_question(composer, context):
    if context.current_questionnaire.is_first_question(context.current_question):
        # started a new questionnaire
        if context.has_answered_questions:
            composer.say("questionnaire finished")

    composer.then_ask(context.current_question)
    return States.ASKING_QUESTION


def recite_answer_ask_correct(composer, context):
    pass  # TODO


def repeat_question(composer, context):
    composer.say("again").ask(context.current_question)
    return States.ASKING_QUESTION


def skip_question(composer, context):
    if context.current_question.is_required:
        composer.say("sorry", "but", "cannot skip this question")
        composer.ask("continue anyway", choices=("affirm", "negate"))
        return "ask_continue_despite_no_skipping"
    else:
        composer.say("skip this question")


def excuse_did_not_understand(composer, context):
    composer.say("sorry", "did not understand")


def abort_claim(composer, context):
    print("CLAIM ABORTED")  # TODO


# TODO: start handler
# TODO: yes = affirm;  no = negate   <-- rename in dialogflow

CONTROLLER_RULES = {
    "stateless": [  # always applied
        IntentHandler(record_phone_damage, intents='phone_broken'),
    ],
    "states": {
        States.INITIAL: [
            IntentHandler(hello, intents=['hello', 'start']),
        ],
        States.SMALLTALK: [
            IntentHandler(ask_to_start),
        ],
        'ask_to_start': [
            IntentHandler(begin_questionnaire, parameters='yes'),
            IntentHandler(user_no_claim, parameters='no'),
        ],
        'ask_continue_despite_no_skipping': [
            IntentHandler(repeat_question, parameters='yes'),
            IntentHandler(abort_claim, parameters='no'),
        ],
        States.ASKING_QUESTION: [
            IntentHandler(clarify, intents='clarify'),
            IntentHandler(skip_question, intents='skip'),
            IntentHandler(check_answer)
        ],
    },
    "fallbacks": [
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(excuse_did_not_understand, intents='fallback'),
    ]
}

rule_controller = Controller(CONTROLLER_RULES)
