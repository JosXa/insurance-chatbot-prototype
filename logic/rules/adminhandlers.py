import os

import time
from logzero import logger as log

import sys

import migrate
from core import Context


def restart_system(r, c: Context):
    if c.user.telegram_id != 62056065:
        return r.say("no permission")
    log.warning("Restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def reset_database(r, c: Context, all=False):
    if c.user.telegram_id != 62056065:
        return r.say("no permission")
    log.warning("Resetting and restarting...")
    migrate.reset_answers()

    if all:
        migrate.clear_redis()
    else:
        migrate.clear_redis(users=[c.user])

    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)
