from functools import wraps

from core import Context
from core.controller import Controller

controller = Controller(warn_bypassed=False)


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


@urge_to_start
def static_smalltalk_response(cp, ctx):
    # This is called when no specific smalltalk handler is set up
    # We take the response from the sentence bank
    intent = ctx.last_user_utterance.intent
    cp.say(intent)


@urge_to_start
def answer_to_how_are_you(r, c):
    intent = c.last_user_utterance.intent
    if intent == 'smalltalk.appraisal.thank_you':
        r.say('with pleasure')
    elif any(intent.startswith(x) for x in ['smalltalk.appraisal', 'smalltalk.user.good']):
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


def bye(r, c):
    r.send_media('tschuess')


def generate_topic(comp, ctx):
    smalltalk_counter = ctx.get_value('smalltalk_counter', 0)
    if smalltalk_counter <= 9:
        comp.say(f"urge to start level {smalltalk_counter - 3}")
