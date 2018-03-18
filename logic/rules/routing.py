from core.controller import AffirmationHandler, IntentHandler, NegationHandler
from logic.rules.claimhandlers import *
from logic.rules.smalltalkhandlers import *

controller = Controller()

all_smalltalk_intents = [
    'who_are_you',
    'tell_a_joke',
    'smalltalk.user.will_be_back',
    'smalltalk.agent.be_clever',
    'smalltalk.user.looks_like',
    'smalltalk.user.joking',
    'smalltalk.greetings.nice_to_talk_to_you',
    'smalltalk.agent.marry_user',
    'smalltalk.agent.talk_to_me',
    'smalltalk.user.has_birthday',
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


def force_return(func, return_value):
    def handler(r, c):
        func(r, c)
        return return_value

    return handler


def evaluate_next_state(func):
    def handler(r, c):
        func(r, c)
        if c.get_value('questionnaire_started'):
            return ask_next_question(r, c)
        return States.SMALLTALK

    return handler


# region  emotion-oriented

# Custom smalltalk handlers
smalltalk_handlers = [
    IntentHandler(congratulate_birthday, intents='smalltalk.user.has_birthday'),
    IntentHandler(bye, intents='smalltalk.greetings.bye'),
]
# All unhandled smalltalk intents are responded to with a static message, as defined in smalltalk.yaml
static_response_intents = [x for x
                           in all_smalltalk_intents
                           if not any(y.contains_intent(x) for y in smalltalk_handlers)]
smalltalk_handlers.append(IntentHandler(
    static_smalltalk_response,
    intents=static_response_intents
))

# Set up all smalltalk handlers to ask the current question if the questionnaire was already started
for h in smalltalk_handlers:
    h.callback = evaluate_next_state(h.callback)

# endregion

# region  dialog-oriented
intro_intents = ['smalltalk.agent.can_you_help', 'clarify']

RULES = {
    "stateless": [  # always applied
        IntentHandler(record_phone_damage, intents='phone_broken'),
        IntentHandler(change_formal_address),
    ],
    "states": {  # triggered when context is in the key's state
        States.SMALLTALK: [
            IntentHandler(start, intents=['start', 'hello', 'smalltalk.greetings']),
            IntentHandler(intro, intents=intro_intents),
            IntentHandler(force_return(intro, States.SMALLTALK), intents=intro_intents),
            IntentHandler(ask_to_start, intents=['phone_broken']),
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
            IntentHandler(clarify, intents=['clarify', 'smalltalk.dialog.what_do_you_mean']),
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
            IntentHandler(start, intents=['start', 'hello', 'smalltalk.greetings']),
            IntentHandler(ask_to_start, intents='phone_broken'),
            IntentHandler(answer_to_how_are_you, intents=['smalltalk.appraisal.good', 'smalltalk.user.can_not_sleep',
                                                          'smalltalk.appraisal.thank_you', 'smalltalk.user.good',
                                                          'smalltalk.user.happy']),
            IntentHandler(answer_to_how_are_you, parameters='feeling'),
        ],
        ('asking', 'should_i_tell_a_joke'): [
            AffirmationHandler(tell_a_joke),
            NegationHandler(too_bad)
        ],
    },
    "fallbacks": [  # triggered if not matching state handler is found
        IntentHandler(intro, intents='what_can_you_do'),
        IntentHandler(user_astonished, intents=['astonishment', 'smalltalk.user.wow']),
        IntentHandler(excuse_did_not_understand, intents='fallback'),
        smalltalk_handlers,
        IntentHandler(no_rule_found),
    ]
}

controller.add_rules_dict(RULES)
