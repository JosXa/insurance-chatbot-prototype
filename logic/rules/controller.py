from core.routing import AffirmationHandler, EmojiHandler, IntentHandler, NegationHandler, RegexHandler, Router, \
    MediaHandler
from logic.intents import SMALLTALK_INTENTS, FEELING_INTENTS, ASTONISHED_AMAZED, REQUEST_HELP
from logic.rules.adminhandlers import *
from logic.rules.claimhandlers import *
from logic.rules.smalltalkhandlers import *

application_router = Router()

# TODO: Remove?
# def force_return(func, return_value):
#     def handler(r, c):
#         func(r, c)
#         return return_value
#
#     return handler
#
#
# def evaluate_next_state(func):
#     def handler(r, c):
#         func(r, c)
#         if c.get_value('claim_started'):
#             return ask_next_question(r, c)
#         return States.SMALLTALK
#
#     return handler


# region  emotion-oriented

# Custom smalltalk handlers
smalltalk_handlers = [
    IntentHandler(congratulate_birthday, intents='smalltalk.user.has_birthday'),
    IntentHandler(bye, intents='smalltalk.greetings.bye'),
]
# All unhandled smalltalk intents are responded to with a static message, as defined in smalltalk.yaml
static_response_intents = [x for x
                           in SMALLTALK_INTENTS
                           if not any(y.contains_intent(x) for y in smalltalk_handlers)]
smalltalk_handlers.append(IntentHandler(
    static_smalltalk_response,
    intents=static_response_intents
))

# TODO: Remove?
# Set up all smalltalk handlers to ask the current question if the questionnaire was already started
# for h in smalltalk_handlers:
#     h.callback = evaluate_next_state(h.callback)

# endregion

# region  dialog-oriented

RULES = {
    "stateless": [  # always applied
        RegexHandler(restart_system, pattern=r'^/r$'),
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(change_formal_address),
    ],
    "dialog_states": {  # triggered when context is in the key's dialog_states
        States.SMALLTALK: [
            IntentHandler(start, intents=['start', 'hello', 'smalltalk.greetings']),
            IntentHandler(intro, intents=REQUEST_HELP),
            IntentHandler(user_no_claim, intents='no_damage'),
            IntentHandler(intro, intents=REQUEST_HELP),
            IntentHandler(ask_to_start, intents=['phone_broken']),
        ],
        'ask_to_start': [
            AffirmationHandler(start_claim),
            IntentHandler(start_claim, intents='phone_broken'),
            IntentHandler(user_no_claim, intents='no_damage'),
            NegationHandler(user_no_claim),
        ],
        'ask_continue_despite_no_skipping': [
            AffirmationHandler(repeat_question),
            NegationHandler(abort_claim),
        ],
        States.ASKING_QUESTION: [
            IntentHandler(clarify, intents=REQUEST_HELP),
            IntentHandler(send_example, intents='example'),
            IntentHandler(skip_question, intents='skip'),
            NegationHandler(skip_question),
            MediaHandler(check_answer),
            IntentHandler(check_answer),
        ],
        'user_confirming_answer': [
            AffirmationHandler(store_answer),
            IntentHandler(repeat_question, intents='repeat'),
            NegationHandler(repeat_question),
            IntentHandler(check_answer)
        ],
        ('asking', 'how_are_you'): [
            IntentHandler(ask_to_start, intents='phone_broken'),
            IntentHandler(answer_to_how_are_you, intents=FEELING_INTENTS),
            IntentHandler(answer_to_how_are_you, parameters='feeling'),
        ],
        ('asking', 'should_i_tell_a_joke'): [
            AffirmationHandler(tell_a_joke),
            NegationHandler(too_bad)
        ],
        'told_joke': [
            IntentHandler(tell_a_joke, intents='again_another')
        ],
        'explained_something': [
            IntentHandler(user_amazed_after_explanation, intents=ASTONISHED_AMAZED),
            NegationHandler(lambda r, c: r.say("now you know"))
        ],
        'previewing_claim': [
            IntentHandler(submit_claim, intents='submit'),
            NegationHandler(claim_needs_editing)
        ]
    },
    "fallbacks": [  # triggered if not matching dialog_states handler is found
        IntentHandler(intro, intents='what_can_you_do'),
        IntentHandler(change_topic, intents='yes'),
        IntentHandler(user_astonished, intents=ASTONISHED_AMAZED),
        EmojiHandler(user_happy, positive=True),  # positive sentiment
        EmojiHandler(neutral_emoji, neutral=True),  # neutral sentiment
        EmojiHandler(user_sad_or_angry, negative=True),  # negative sentiment
        EmojiHandler(change_topic),  # any emoji
        smalltalk_handlers,
    ]
}

application_router.add_rules_dict(RULES)
