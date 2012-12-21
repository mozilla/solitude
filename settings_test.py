# test_utils picks this file up for testing.
import os
from solitude.settings.base import *

filename = os.path.join(os.path.dirname(__file__), 'sample.key')

AES_KEYS = {
    'buyerpaypal:key': filename,
    'sellerpaypal:id': filename,
    'sellerpaypal:token': filename,
    'sellerpaypal:secret': filename,
    'sellerproduct:secret': filename,
}

SOLITUDE_PROXY = False

PAYPAL_MOCK = False
PAYPAL_PROXY = False
PAYPAL_URL_WHITELIST = ('https://marketplace-dev.allizom.org',)

# How tastypie processes error depends upon these settings.
DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
TASTYPIE_FULL_DEBUG = DEBUG

DUMP_REQUESTS = False

HMAC_KEYS = {'2011-01-01': 'cheesecake'}
from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)

# Celery.
CELERY_ALWAYS_EAGER = True

# Send all statsd to nose.
STATSD_CLIENT = 'django_statsd.clients.nose'

# No need for paranoia in tests.
from django_paranoia.signals import process
process.disconnect(dispatch_uid='paranoia.reporter.django_paranoia'
                                '.reporters.cef_')
process.disconnect(dispatch_uid='paranoia.reporter.django_paranoia'
                                '.reporters.log')
DJANGO_PARANOIA_REPORTERS = []
