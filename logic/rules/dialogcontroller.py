from core.routing import AffirmationHandler, EmojiHandler, IntentHandler, MediaHandler, NegationHandler, RegexHandler, \
    Router
from logic.intents import ASTONISHED_AMAZED, REQUEST_HELP, SMALLTALK_INTENTS, START
from logic.rules.adminhandlers import *
from logic.rules.claimhandlers import *
from logic.rules.smalltalkhandlers import *

application_router = Router()

# Custom smalltalk handlers
smalltalk_handlers = [
    IntentHandler(congratulate_birthday, intents='smalltalk.user.has_birthday'),
    IntentHandler(bye, intents='smalltalk.greetings.bye'),
]
# All unhandled smalltalk intents are responded to with a static message, as defined in smalltalk-aggregated.yaml
static_response_intents = [x for x
                           in SMALLTALK_INTENTS
                           if not any(y.contains_intent(x) for y in smalltalk_handlers)]
smalltalk_handlers.append(IntentHandler(
    static_smalltalk_response,
    intents=static_response_intents
))

# region  dialog-oriented

RULES = {
    "stateless": [  # always viable
        RegexHandler(restart_system, pattern=r'^/r$'),
        RegexHandler(lambda r, c: reset_database(r, c, all=True), pattern=r'^/resetall$'),
        RegexHandler(reset_database, pattern=r'^/reset$'),
        RegexHandler(send_questionnaires, pattern=r'^/query$'),
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(change_formal_address),
    ],
    "dialog_states": {  # triggered when context is in the key's dialog_states
        States.SMALLTALK: [
            IntentHandler(start, intents=START),
            IntentHandler(intro, intents=REQUEST_HELP),
            IntentHandler(user_no_claim, intents='no_damage'),
            IntentHandler(ask_to_start, intents='phone_broken'),
            IntentHandler(another_time, intents='skip'),
        ],
        'ask_to_start': [
            AffirmationHandler(start_claim),
            IntentHandler(start_claim, intents='phone_broken'),
            IntentHandler(user_no_claim, intents='no_damage'),
            NegationHandler(user_no_claim),
        ],
        'ask_continue_despite_no_skipping': [
            AffirmationHandler(repeat_question),
            IntentHandler(repeat_question, intents='phone_broken'),
            NegationHandler(abort_claim),
            IntentHandler(abort_claim, intents='no_damage'),
        ],
        States.ASKING_QUESTION: [
            IntentHandler(clarify, intents=REQUEST_HELP),
            IntentHandler(static_smalltalk_response, intents='smalltalk.appraisal.thank_you'),
            IntentHandler(send_example, intents='example'),
            IntentHandler(skip_question, intents='skip'),
            NegationHandler(skip_question),
            MediaHandler(check_answer),
            IntentHandler(check_answer),
        ],
        'user_confirming_answer': [
            AffirmationHandler(store_answer),
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
        'explanation_given': [
            IntentHandler(user_amazed_after_explanation, intents=ASTONISHED_AMAZED),
            NegationHandler(lambda r, c: r.say("now you know"))
        ],
        'previewing_claim': [
            IntentHandler(submit_claim, intents='submit'),
            NegationHandler(claim_needs_editing)
        ]
    },
    "fallbacks": [  # triggered if no matching dialog_states handler is found
        IntentHandler(intro, intents='what_can_you_do'),
        IntentHandler(change_topic, intents='yes'),
        IntentHandler(user_astonished, intents=ASTONISHED_AMAZED),
        EmojiHandler(user_happy, positive=True),  # positive sentiment
        EmojiHandler(neutral_emoji, neutral=True),  # neutral sentiment
        EmojiHandler(user_sad_or_angry, negative=True),  # negative sentiment
        EmojiHandler(change_topic),  # any emoji
        IntentHandler(sudo_make_sandwich, intents='smalltalk.agent.sudo_make_sandwich'),  # easteregg
        smalltalk_handlers,
    ]
}

application_router.add_rules_dict(RULES)
