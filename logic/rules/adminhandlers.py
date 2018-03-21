import os

import time
from logzero import logger as log

import sys

from core import Context


def restart_system(r, c: Context):
    if c.user.telegram_id != 62056065:
        return
    log.warning("Restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)
