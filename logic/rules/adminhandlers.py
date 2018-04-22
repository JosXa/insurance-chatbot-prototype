import os

import time
from pprint import pprint

from logzero import logger as log

import sys

import migrate
from core import Context
from core.dialogmanager import ForceReevaluation, StopPropagation
from model import User, UserAnswers


def restart_system(r, c: Context):
    if c.user.telegram_id != 62056065:
        return r.say("no permission")
    log.warning("Restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def reset_database(r, c: Context, for_all=False):
    log.info("Resetting")
    if c.get("reset") is not None:
        r.say("system reset", parameters={"n_reset": c.get("reset")})
        c["reset"] = None
        raise StopPropagation

    if for_all and c.user.telegram_id != 62056065:
        return r.say("no permission")

    users = None if for_all else [c.user]
    log.warning(f"Resetting and restarting for {'all' if all else [str(u) for u in users]}...")

    # First reset answers, then context
    n_reset = migrate.reset_answers(users)
    # migrate.clear_redis(users)
    c.reset_all()

    c["reset"] = n_reset

    raise ForceReevaluation


def send_questionnaires(r, c: Context):
    for u in User.select():
        all_answers = UserAnswers.get_name_answer_dict(u)
        if all_answers:
            r.say(
                "preview claim",
                parameters=dict(answers=all_answers)
            )
