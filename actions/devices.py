from clients.botapiclients import IBotAPIClient
from corpus import DEVICES
from logic.context import UserContexts
from model import User


def ask_phone_model(client: IBotAPIClient, user: User, context: UserContexts):
    markup = client.create_reply_keyboard(x['name'] for x in DEVICES)
    msg = client._send_message(user, "Welches Gerät haben Sie denn?", markup=markup)
    context.add_outgoing_action(msg)
