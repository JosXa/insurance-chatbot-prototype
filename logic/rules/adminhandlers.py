import os

import time
from pprint import pprint

from logzero import logger as log

import sys

import migrate
from core import Context
from model import User, UserAnswers


def restart_system(r, c: Context):
    if c.user.telegram_id != 62056065:
        return r.say("no permission")
    log.warning("Restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def reset_database(r, c: Context, all=False):
    if all and c.user.telegram_id != 62056065:
        return r.say("no permission")
    log.warning("Resetting and restarting...")
    migrate.reset_answers()

    if all:
        migrate.clear_redis()
    else:
        migrate.clear_redis(users=[c.user])

    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def send_questionnaires(r, c: Context):
    for u in User.select():
        all_answers = UserAnswers.get_name_answer_dict(u)
        pprint(all_answers)
        r.say(
            "preview claim",
            parameters=dict(answers=all_answers)
        )
