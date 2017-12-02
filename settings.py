import os
DATABASE_URL = os.environ.get('DATABASE_URL', os.path.expanduser('~/data/'))

DIALOGFLOW_ACCESS_TOKEN = '57d6b837eb594919b0a35290387a3020'

FACEBOOK_ACCESS_TOKEN = 'KEK'

TELEGRAM_ACCESS_TOKEN = '324133401:AAHVjjXotCDXC_kIIkfM0O6bm9-l7BfJw-I'
TELEGRAM_WEBHOOK_URL = 'https://bachelor-thesis.herokuapp.com/'
TELEGRAM_WEBHOOK_PORT = os.environ.get('PORT', 5000)


