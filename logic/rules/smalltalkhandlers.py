import random
from functools import wraps

from core import Context
from core.controller import Controller
from logic.rules.progresstracker import progress, on_progress_threshold

controller = Controller(warn_bypassed=False)

RANDOM_QUESTIONS = {
    "should i tell a joke": ("asking", "should_i_tell_a_joke", 1),  # lifetime of 1 utterance
    "how can i help": None
}


def urge_to_start(func):
    """
    Decorator to count the number of smalltalk handlers executed.
    Urges the user to start his claim the more smalltalk has been performed.
    """

    @wraps(func)
    def wrapped(composer, context: Context):
        if not context.get_value('user_no_claim', False):
            new_value = context.get_value('smalltalk_counter', 0) + 1
            context.set_value('smalltalk_counter', new_value)
            if new_value >= 4:
                result = func(composer, context)
                generate_topic(composer, context)
                return result
        return func(composer, context)

    return wrapped


# TODO: add argument instead of an own decorator to control the checker-callback
@progress("smalltalk")
def static_smalltalk_response(cp, ctx):
    # This is called when no specific smalltalk handler is set up
    # We take the response from the sentence bank
    intent = ctx.last_user_utterance.intent
    cp.say(intent)


def fallback_smalltalk(cp, ctx):
    return ask_random_question(cp, ctx)


def ask_random_question(cp, ctx):
    asked_questions = ctx.setdefault('random_questions', set())

    try:
        # Get next unasked question
        question = next(q for q in RANDOM_QUESTIONS.items() if q[0] not in asked_questions)
    except StopIteration:
        question = random.choice(RANDOM_QUESTIONS)

    intent, return_value = question
    cp.then_ask(intent)
    asked_questions.add(intent)
    return return_value


@urge_to_start
def answer_to_how_are_you(r, c):
    intent = c.last_user_utterance.intent
    if intent == 'smalltalk.appraisal.thank_you':
        r.say('with pleasure')
    elif any(intent.startswith(x) for x in ['smalltalk.appraisal', 'smalltalk.user.good', 'smalltalk.user.happy']):
        r.say('glad to hear that', 'i feel good')
    else:
        feeling = c.last_user_utterance.parameters
        if feeling:
            print(feeling)
        else:
            try:
                return static_smalltalk_response(r, c)
            except:
                r.say('interesting')


def congratulate_birthday(r, c):
    r.send_media('happy birthday')


def too_bad(r, c):
    r.say('too_bad', 'how_else_can_i_help')


def tell_a_joke(r, c):
    r.say('tell_a_joke')


def bye(r, c):
    r.send_media('tschuess')


def generate_topic(comp, ctx):
    smalltalk_counter = ctx.get_value('smalltalk_counter', 0)
    if smalltalk_counter <= 7:
        comp.say(f"urge to start level {smalltalk_counter - 3}")
