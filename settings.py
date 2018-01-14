import os
PORT = os.environ.get('PORT', 5000)

APP_URL = 'https://bachelor-thesis.herokuapp.com/'
TEST_MODE = bool(os.environ.get("DEBUG", False))

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://zudibytvipthsa:c8c2d7f0bbe8da76cdd1b66375d0d4c56f9c8d98447f9ace26aa09eec3dcc4bd@ec2-79-125-13-42.eu-west-1.compute.amazonaws.com:5432/ddhs2ptave6514')

DIALOGFLOW_ACCESS_TOKEN = '57d6b837eb594919b0a35290387a3020'

FACEBOOK_ACCESS_TOKEN = 'EAACJPDO6INEBALMOSECRRfwYKlYCNteaKtKh9QASJp9DWEVZAHjQDcBg8alI8QtStLVGjlKTDONs2ldyZC56RFZAq8HE9FQP7XNdgsuBttH8xMY7rBVa74ZCdJNN8JXwCFjGDWQZCgksqjD5L9RVaq3dZCiD5a8ZBp11hF04y1dCXmHBmdUqvhW'

TELEGRAM_ACCESS_TOKEN = '480873241:AAE5m0ymhMsUGFhQehveFN3Htm1_v8X90JA'


