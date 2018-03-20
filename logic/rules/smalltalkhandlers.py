import random
from functools import wraps

from logzero import logger as log

from core import Context
from logic.rules.progresstracker import get_progress, progress

RANDOM_QUESTIONS = {
    "should i tell a joke": ("asking", "should_i_tell_a_joke", 1),  # lifetime of 1 utterance
    "how can i help": None
}


def change_topic_on_threshold(func):
    """
    Decorator to count the number of smalltalk handlers executed.
    Urges the user to start his claim the more smalltalk has been performed.
    """

    @wraps(func)
    def wrapped(composer, context: Context):
        if not context.get_value('user_no_claim', False):
            if get_progress(context, "smalltalk") >= 2:
                result = func(composer, context)
                # First enter the next dialog state result (probably None anyway)
                context.dialog_states.put(result)
                # Then return the next dialog state of the changed topic
                return change_topic(composer, context)

        wrapped.__name__ = func.__name__
        return func(composer, context)

    return wrapped


# TODO: add argument instead of an own decorator to control the checker-callback
@progress("smalltalk")
@change_topic_on_threshold
def static_smalltalk_response(cp, ctx):
    # This is called when no specific smalltalk handler is set up
    # We take the response from the sentence bank
    intent = ctx.last_user_utterance.intent
    cp.say(intent)


def fallback_smalltalk(r, c):
    return change_topic(r, c)


def change_topic(r, c):
    asked_questions = c.setdefault('random_questions', set())

    try:
        # Get next unasked question
        question = next(q for q in RANDOM_QUESTIONS.items() if q[0] not in asked_questions)
    except StopIteration:
        # Random choice if all have been asked
        key = random.choice(list(RANDOM_QUESTIONS.keys()))
        question = key, RANDOM_QUESTIONS[key]

    intent, return_value = question
    r.then_ask(intent)
    asked_questions.add(intent)
    log.error(question)
    return return_value


@progress("smalltalk")
@change_topic_on_threshold
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
    return "told_joke", 2


def bye(r, c):
    r.send_media('tschuess')
