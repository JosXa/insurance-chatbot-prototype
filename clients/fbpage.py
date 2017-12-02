import logging

from decouple import config
from fbmq import Page

import settings

log = logging.getLogger()
page = Page(settings.FB_ACCESS_TOKEN)


@page.after_send
def after_send(payload, response):
    log.debug('AFTER_SEND : ' + payload.to_json())
    log.debug('RESPONSE : ' + response.text)