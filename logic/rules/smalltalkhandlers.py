from functools import wraps

from core import Context, ChatAction
from logic.intents import FEELING_INTENTS
from logic.responsecomposer import ResponseComposer
from logic.rules.claimhandlers import chance
from logic.rules.progresstracker import get_progress, progress

ORDERED_TOPICS = {
    # { intent:  return_value }
    "should i tell a joke": ("asking", "should_i_tell_a_joke", 1),  # lifetime of 1 utterance
    "smartphone_damage_explanation": ('explanation_given', 1),
    "urge_to_start": None,
    "only_helpful_for_claims": None,
    "how can i help": None,
}


def change_topic_on_threshold(func):
    """
    Decorator to count the number of smalltalk handlers executed.
    Urges the user to start his claim the more smalltalk has been performed.
    """

    @wraps(func)
    def wrapped(composer, context: Context):
        if not context.get('user_no_claim', False):
            if get_progress(context, "smalltalk") >= 2:
                result = func(composer, context)
                # First enter the next dialog state result (probably None anyway)
                context.dialog_states.put(result)

                if not context.get("claim_started", False):
                    # Then return the next dialog state of the changed topic
                    return change_topic(composer, context)

        wrapped.__name__ = func.__name__
        return func(composer, context)

    return wrapped


# TODO: add argument instead of an own decorator to control the checker-callback
@progress("smalltalk")
@change_topic_on_threshold
def static_smalltalk_response(r, c):
    # This is called when no specific smalltalk handler is set up
    # We take the response from the sentence bank
    intent = c.last_user_utterance.intent
    r.say(intent)


def wait_for_user(r, c):
    r.say("ok waiting")


def fallback_smalltalk(r, c):
    return change_topic(r, c)


def change_topic(r, c):
    asked_questions = c.setdefault('random_questions', set())

    if c.get("no_claim", False):
        r.say("random topic")
        return

    try:
        # Get next unasked question
        question = next(q for q in ORDERED_TOPICS.items() if q[0] not in asked_questions)
    except StopIteration:
        # Random choice if all have been asked
        r.say("random topic")
        return

    intent, return_value = question
    r.then_ask(intent, delay=ChatAction.Delay.MEDIUM)
    asked_questions.add(intent)
    return return_value


@progress("smalltalk")
@change_topic_on_threshold
def answer_to_how_are_you(r, c):
    intent = c.last_user_utterance.intent
    if intent == 'smalltalk.appraisal.thank_you':
        r.say('with pleasure', 'i feel good')
    elif intent in FEELING_INTENTS:
        return answer_user_feeling(r, c)
    else:
        feeling = c.last_user_utterance.parameters
        if feeling:
            print(feeling)
        else:
            try:
                return static_smalltalk_response(r, c)
            except:
                r.say('interesting')


def answer_user_feeling(r, c):
    intent = c.last_user_utterance.intent
    if any(intent.startswith(x) for x in ['smalltalk.appraisal.good', 'smalltalk.user.good',
                                          'smalltalk.user.happy']):
        r.say('glad to hear that', 'i feel good')
    elif any(intent.startswith(x) for x in ['smalltalk.appraisal.bad', 'smalltalk.user.sad']):
        r.say('oh_no_user_sad')
    elif intent == 'smalltalk.user.sick':
        static_smalltalk_response(r, c)


def congratulate_birthday(r, c):
    r.send_media('happy birthday')


def too_bad(r, c):
    r.say('too_bad', 'how_else_can_i_help')


def tell_a_joke(r, c):
    r.say('tell_a_joke')
    return "told_joke", 2


def bye(r, c):
    r.send_media('tschuess')


def user_happy(r, c):
    r.say("glad to see user happy")


def neutral_emoji(r, c):
    r.say("neutral feeling")


def user_sad_or_angry(r, c):
    r.say("allay")


def user_amazed_after_explanation(r, c):
    r.say("pretty cool huh")


def another_time(r, c):
    r.say("another time")


def sudo_make_sandwich(r: ResponseComposer, c):
    r.send_media('sandwich', caption_intent='here you go')


def no_rule_found(r, c):
    r.say("sorry", "what i understood", parameters={'understanding': c.last_user_utterance.intent})
    if c.get('claim_started', False):
        return
    if chance(0.6):
        return change_topic(r, c)
    else:
        r.say("ask something else")
