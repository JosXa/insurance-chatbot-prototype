import random

from logzero import logger

from corpus.responsecomposer import ResponseComposer
from logic.context import Context, States
from logic.controller import AffirmationHandler, Controller, IntentHandler, NegationHandler
from logic.smalltalk import smalltalk_controller
from model import UserAnswers


def probability(value: float) -> bool:
    return random.random() < value


def hello(composer, context):
    # TODO: If user has already interacted (after bot restart), go immediately to "current" question
    composer.say("hello")
    if not context.has_outgoing_intent("what i can do", age_limit=10):
        composer.say("what i can do")
    return States.SMALLTALK


def ask_to_start(composer, context):
    composer.ask("claim damage", choices=['affirm_yes', 'negate_no'])
    return 'ask_to_start'


def record_phone_damage(composer, context):
    composer.say("sorry for that")
    dmg_type = context.last_user_utterance.parameters.get('damage_type')
    if dmg_type:
        context.add_answer_to_question('damage_type', str(dmg_type))


def begin_questionnaire(composer, context):
    composer.say("with pleasure").then_ask(context.current_question)
    return States.ASKING_QUESTION


def user_no_claim(composer, context):
    print("user has no claim to make")  # TODO


def send_example(composer, context):
    composer.give_example(context.current_question)


def clarify(composer, context: Context):
    should_send_example = False
    if context.last_user_utterance.intent == 'example':
        should_send_example = True

    if context.has_outgoing_intent('give_hint', age_limit=2):
        should_send_example = True
    else:
        composer.give_hint(context.current_question)

    if should_send_example:
        send_example(composer, context)


def check_answer(composer, context):
    question = context.current_question
    if question.is_valid(context.last_user_utterance.text):
        if question.confirm:
            return ask_to_confirm_answer(composer, context)
        else:
            return store_answer(composer, context, user_answer=context.last_user_utterance.text)
    else:
        composer.say('sorry', 'invalid answer').give_hint(question)
        return States.ASKING_QUESTION


def store_answer(composer, context, user_answer=None):
    # Assumes answer is checked for validity
    if not user_answer:
        user_answer = context.get_value('user_answer')
    context.add_answer_to_question(context.current_question, user_answer)
    composer.say("ok thank you")
    return ask_next_question(composer, context)


def ask_to_confirm_answer(composer: ResponseComposer, context):
    composer.ask_to_confirm(context.current_question, context.last_user_utterance.text)
    context.set_value('user_answer', context.last_user_utterance)
    return 'confirming_user_answer'


def ask_next_question(composer, context):
    if context.current_questionnaire.is_first_question(context.current_question):
        # started a new questionnaire
        if context.has_answered_questions:
            composer.say("questionnaire finished")

    composer.then_ask(context.current_question)
    return States.ASKING_QUESTION


def repeat_question(composer, context):
    composer.say("again").ask(context.current_question)
    return States.ASKING_QUESTION


def skip_question(composer, context):
    if context.current_question.is_required:
        composer.say("sorry", "but", "cannot skip this question")
        composer.ask("continue anyway", choices=("affirm_yes", "negate_no"))
        return "ask_continue_despite_no_skipping"
    else:
        composer.say("skip this question", parameters={'question': context.current_question})
        context.add_answer_to_question(context.current_question, UserAnswers.NO_ANSWER)
        ask_next_question(composer, context)


def excuse_did_not_understand(composer, context):
    composer.say("sorry", "but", "did not understand")
    if probability(0.8) and context.questionnaire_completion_ratio > 0.3:
        composer.say("try again")


def abort_claim(composer, context):
    print("CLAIM ABORTED")  # TODO


def change_formal_address(composer, context):
    formal = None
    address = None
    if context.last_user_utterance.parameters:
        address = context.last_user_utterance.parameters.get('formal_address')
    if address:
        if address == 'yes':
            formal = True
        elif address == 'false':
            formal = False
        else:
            logger.warning(f'Invalid formal_address value: {address}')
            return
    else:
        # TODO: Not properly detected in DialogFlow, because there is no easy way to add this entity to every intent.
        if any(x in context.last_user_utterance.text.lower() for x in ('du', 'dein')):
            formal = False
        elif any(x in context.last_user_utterance.text for x in ('Ihr', 'Sie')):
            formal = True

    if formal is not None:
        logger.debug(f"{context.user.name} is now addressed {'formally' if formal else 'informally'}.")
        context.user.update(formal_address=formal).execute()


# TODO: start handler
# TODO: yes = affirm;  no = negate   <-- rename in dialogflow

CLAIM_RULES = {
    "stateless": [  # always applied
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(change_formal_address),
    ],
    "states": {
        States.INITIAL: [
            IntentHandler(hello, intents=['hello', 'start']),
        ],
        States.SMALLTALK: [
            IntentHandler(ask_to_start),
        ],
        'ask_to_start': [
            AffirmationHandler(begin_questionnaire),
            NegationHandler(user_no_claim),
        ],
        'ask_continue_despite_no_skipping': [
            AffirmationHandler(repeat_question),
            NegationHandler(abort_claim),
        ],
        States.ASKING_QUESTION: [
            IntentHandler(clarify, intents='clarify'),
            IntentHandler(send_example, intents='example'),
            IntentHandler(skip_question, intents='skip'),
            NegationHandler(skip_question),
            IntentHandler(check_answer)
        ],
        'confirming_user_answer': [
            AffirmationHandler(store_answer),
            IntentHandler(repeat_question, intents='repeat'),
            NegationHandler(repeat_question),
            IntentHandler(check_answer)
        ],
    },
    "fallbacks": [
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(excuse_did_not_understand, intents='fallback'),
    ]
}

rule_controller = Controller(CLAIM_RULES)
