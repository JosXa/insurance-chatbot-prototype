import random

from logzero import logger

from corpus.sentencecomposer import SentenceComposer
from logic.context import Context, States
from logic.controller import AffirmationHandler, Controller, IntentHandler, NegationHandler
from model import UserAnswers

controller = Controller()


def probability(value: float) -> bool:
    return random.random() < value


@controller.on_intent(States.INITIAL, intents=['hello', 'start'])
def hello(c, ctx):
    # TODO: If user has already interacted (after bot restart), go immediately to "current" question
    c.say("hello")
    if not ctx.has_outgoing_intent("what i can do", age_limit=10):
        c.say("what i can do")
        c.say("what you can say")
    return States.SMALLTALK


def ask_to_start(c, ctx):
    c.ask("claim damage", choices=['affirm_yes', 'negate_no'])
    return 'ask_to_start'


def record_phone_damage(c, ctx):
    c.say("sorry for that")
    dmg_type = ctx.last_user_utterance.parameters.get('damage_type')
    if dmg_type:
        ctx.add_answer_to_question('damage_type', str(dmg_type))


def begin_questionnaire(c, ctx):
    c.say("with pleasure").then_ask(ctx.current_question)
    return States.ASKING_QUESTION


def user_no_claim(c, ctx):
    print("user has no claim to make")  # TODO


def send_example(c, ctx):
    c.give_example(ctx.current_question)


def clarify(c, ctx: Context):
    should_send_example = False
    if ctx.last_user_utterance.intent == 'example':
        should_send_example = True

    if ctx.has_outgoing_intent('give_hint', age_limit=2):
        should_send_example = True
    else:
        c.give_hint(ctx.current_question)

    if should_send_example:
        send_example(c, ctx)


def check_answer(c, ctx):
    question = ctx.current_question
    if question.is_valid(ctx.last_user_utterance.text):
        if question.confirm:
            return ask_to_confirm_answer(c, ctx)
        else:
            return store_answer(c, ctx, user_answer=ctx.last_user_utterance.text)
    else:
        c.say('sorry', 'invalid answer').give_hint(question)
        return States.ASKING_QUESTION


def store_answer(c, ctx, user_answer=None):
    # Assumes answer is checked for validity
    if not user_answer:
        user_answer = ctx.get_value('user_answer')
    ctx.add_answer_to_question(ctx.current_question, user_answer)
    c.say("ok thank you")
    return ask_next_question(c, ctx)


def ask_to_confirm_answer(c: SentenceComposer, ctx):
    c.ask_to_confirm(ctx.current_question, ctx.last_user_utterance.text)
    ctx.set_value('user_answer', ctx.last_user_utterance)
    return 'confirming_user_answer'


def ask_next_question(c, ctx):
    if ctx.current_questionnaire.is_first_question(ctx.current_question):
        # started a new questionnaire
        if ctx.has_answered_questions:
            c.say("questionnaire finished")

    c.then_ask(ctx.current_question)
    return States.ASKING_QUESTION


def repeat_question(c, ctx):
    c.say("again").ask(ctx.current_question)
    return States.ASKING_QUESTION


def skip_question(c, ctx):
    if ctx.current_question.is_required:
        c.say("sorry", "but", "cannot skip this question")
        c.ask("continue anyway", choices=("affirm_yes", "negate_no"))
        return "ask_continue_despite_no_skipping"
    else:
        c.say("skip this question", parameters={'question': ctx.current_question})
        ctx.add_answer_to_question(ctx.current_question, UserAnswers.NO_ANSWER)
        ask_next_question(c, ctx)


def excuse_did_not_understand(c, ctx):
    c.say("sorry", "but", "did not understand")
    if probability(0.8) and ctx.questionnaire_completion_ratio > 0.3:
        c.say("reformulate")


def abort_claim(c, ctx):
    print("CLAIM ABORTED")  # TODO


def change_formal_address(c, ctx: Context):
    if ctx.last_user_utterance.parameters:
        address = ctx.last_user_utterance.parameters.get('formal_address')
        if address:
            if address == 'yes':
                ctx.user.formal_address = True
            elif address == 'false':
                ctx.user.formal_address = False
                c.say("we say du")
            else:
                logger.warning(f'Invalid formal_address value: {address}')
                return
    else:
        if any(x in ctx.last_user_utterance.text.lower() for x in ('du', 'dein')):
            ctx.user.formal_address = False
            c.say("we say du")
        elif any(x in ctx.last_user_utterance.text for x in ('Ihr', 'Sie', 'Ihnen')):
            ctx.user.formal_address = True
    ctx.user.save()


def no_rule_found(c, ctx):
    c.say("sorry", "what i understood", parameters={'understanding': ctx.last_user_utterance.intent})
    c.say("ask something else")

    # TODO: start handler
    # TODO: yes = affirm;  no = negate   <-- rename in dialogflow


RULES = {
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
        IntentHandler(no_rule_found),
    ]
}

controller.add_rules_dict(RULES)
