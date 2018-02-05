import json
import os

import sys
from decouple import config

PORT = config('PORT', cast=int, default=5000)
APP_URL = 'https://bachelor-thesis.herokuapp.com/'
TEST_MODE = config('DEBUG', cast=bool, default=False)

# CLOUDCONVERT_ACCESS_TOKEN = config('CLOUDCONVERT_ACCESS_TOKEN')
DIALOGFLOW_ACCESS_TOKEN = config('DIALOGFLOW_ACCESS_TOKEN')
GOOGLE_VOICE_TOKEN = config('DATABASE_URL')
FACEBOOK_ACCESS_TOKEN = config('FACEBOOK_ACCESS_TOKEN')
TELEGRAM_ACCESS_TOKEN = config('TELEGRAM_ACCESS_TOKEN')
TWILIO_ACCESS_TOKEN = config('TWILIO_ACCESS_TOKEN')
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
DATABASE_URL = config('DATABASE_URL')

# Insert google private key into configuration json and add it to environment vars
# service_account_key = config('GOOGLE_SERVICE_ACCOUNT_KEY')
# creds = json.load(open("/home/joscha/auth/service-account-file.json", "r"))
# print(creds['private_key'])
# print(json.load(open('google-service-account.json', 'r'))['private_key'])
# creds["private_key"] = service_account_key
# filename = 'google-service-account.json'
# json.dump(creds, open(filename, 'w'), ensure_ascii=False)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'service-account-file.json'

ENABLE_CONVERSATION_RECORDING = TEST_MODE

CONTEXT_LOOKUP_RECENCY = 15
