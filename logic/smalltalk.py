from logic.controller import Controller, IntentHandler


def test(composer, context):
    print('YESYESYES')
    composer.say("yes", "yes", "yes")


SMALLTALK_RULES = {
    "stateless": [
        IntentHandler(test),
    ],
    "states": {
    },
    "fallbacks": [
    ]
}

smalltalk_controller = Controller(SMALLTALK_RULES)
