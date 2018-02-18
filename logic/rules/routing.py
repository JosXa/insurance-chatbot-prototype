from pprint import pprint

from core.controller import AffirmationHandler, IntentHandler, NegationHandler
from logic.rules.claimhandlers import *
from logic.rules.smalltalkhandlers import *

controller = Controller()

all_smalltalk_intents = [
    'tell_a_joke',
    'smalltalk.user.will_be_back',
    'smalltalk.agent.be_clever',
    'smalltalk.user.looks_like',
    'smalltalk.user.joking',
    'smalltalk.greetings.nice_to_talk_to_you',
    'smalltalk.agent.marry_user',
    'smalltalk.agent.talk_to_me',
    'smalltalk.user.has_birthday',
    'smalltalk.dialog.wrong',
    'smalltalk.user.wants_to_see_agent_again',
    'smalltalk.user.happy',
    'smalltalk.greetings.whatsup',
    'smalltalk.agent.acquaintance',
    'smalltalk.greetings.goodnight',
    'smalltalk.user.lonely',
    'smalltalk.emotions.wow',
    'smalltalk.appraisal.bad',
    'smalltalk.agent.funny',
    'smalltalk.agent.birth_date',
    'smalltalk.agent.occupation',
    'smalltalk.appraisal.no_problem',
    'smalltalk.agent.age',
    'smalltalk.user.going_to_bed',
    'smalltalk.user.bored',
    'smalltalk.agent.bad',
    'smalltalk.user.misses_agent',
    'smalltalk.agent.beautiful',
    'smalltalk.user.testing_agent',
    'smalltalk.appraisal.good',
    'smalltalk.agent.there',
    'smalltalk.agent.annoying',
    'smalltalk.greetings.bye',
    'smalltalk.user.angry',
    'smalltalk.agent.busy',
    'smalltalk.dialog.sorry',
    'smalltalk.agent.right',
    'smalltalk.appraisal.welcome',
    'smalltalk.agent.suck',
    'smalltalk.agent.happy',
    'smalltalk.user.busy',
    'smalltalk.user.excited',
    'smalltalk.appraisal.well_done',
    'smalltalk.agent.hobby',
    'smalltalk.agent.family',
    'smalltalk.agent.clever',
    'smalltalk.agent.ready',
    'smalltalk.greetings.nice_to_see_you',
    'smalltalk.dialog.i_do_not_care',
    'smalltalk.user.wants_to_talk',
    'smalltalk.greetings.how_are_you',
    'smalltalk.agent.sure',
    'smalltalk.emotions.ha_ha',
    'smalltalk.agent.my_friend',
    'smalltalk.user.waits',
    'smalltalk.agent.real',
    'smalltalk.appraisal.thank_you',
    'smalltalk.dialog.what_do_you_mean',
    'smalltalk.user.back',
    'smalltalk.agent.origin',
    'smalltalk.agent.good',
    'smalltalk.agent.drunk',
    'smalltalk.agent.chatbot',
    'smalltalk.dialog.hug',
    'smalltalk.user.does_not_want_to_talk',
    'smalltalk.greetings.start',
    'smalltalk.user.sleepy',
    'smalltalk.user.tired',
    'smalltalk.greetings.nice_to_meet_you',
    'smalltalk.greetings.goodevening',
    'smalltalk.agent.answer_my_question',
    'smalltalk.user.sad',
    'smalltalk.agent.boss',
    'smalltalk.agent.can_you_help',
    'smalltalk.agent.crazy',
    'smalltalk.user.likes_agent',
    'smalltalk.agent.residence',
    'smalltalk.user.can_not_sleep',
    'smalltalk.agent.fired',
    'smalltalk.agent.date_user',
    'smalltalk.agent.hungry',
    'smalltalk.agent.boring',
    'smalltalk.dialog.hold_on',
    'smalltalk.user.good',
    'smalltalk.greetings.goodmorning',
    'smalltalk.user.needs_advice',
    'smalltalk.user.loves_agent',
    'smalltalk.user.here']

### region  EMOTION-ORIENTED
# Custom smalltalk handlers
smalltalk_handlers = [
    IntentHandler(congratulate_birthday, intents='smalltalk.user.has_birthday'),
]
# All unhandled smalltalk intents are responded to with a static message, as defined in smalltalk.yaml
static_response_intents = [x for x
                           in all_smalltalk_intents
                           if not any(y.contains_intent(x) for y in smalltalk_handlers)]
smalltalk_handlers.append(IntentHandler(
    static_smalltalk_response,
    intents=static_response_intents
))
# endregion

### region  TASK-ORIENTED


# endregion

RULES = {
    "stateless": [  # always applied
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(change_formal_address),
    ],
    "states": {
        States.INITIAL: [
            IntentHandler(start, intents=['start', 'hello', 'smalltalk.greetings']),
            smalltalk_handlers,
        ],
        'smalltalk': [
            smalltalk_handlers,
            IntentHandler(ask_to_start),
        ],
        'ask_to_start': [
            AffirmationHandler(begin_questionnaire),
            IntentHandler(user_no_claim, intents='no_damage'),
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
        'user_confirming_answer': [
            AffirmationHandler(store_answer),
            IntentHandler(repeat_question, intents='repeat'),
            NegationHandler(repeat_question),
            IntentHandler(check_answer)
        ],
        ('asking', 'how_are_you'): [
            IntentHandler(ask_to_start, intents='phone_broken'),
            IntentHandler(answer_to_how_are_you, intents=['smalltalk.appraisal.good', 'smalltalk.user.can_not_sleep']),
            IntentHandler(answer_to_how_are_you, parameters='feeling'),
            smalltalk_handlers
        ]
    },
    "fallbacks": [
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(excuse_did_not_understand, intents='fallback'),
        IntentHandler(no_rule_found),
    ]
}

controller.add_rules_dict(RULES)