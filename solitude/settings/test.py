# test_utils picks this file up for testing.
import atexit
import os
import shutil
from tempfile import gettempdir

from solitude.settings.base import *

filename = os.path.join(os.path.dirname(__file__), 'sample.key')

AES_KEYS = {
    'buyerpaypal:key': filename,
    'buyeremail:key': filename,
    'sellerpaypal:id': filename,
    'sellerpaypal:token': filename,
    'sellerpaypal:secret': filename,
    'sellerproduct:secret': filename,
    'bango:signature': filename,
}

SOLITUDE_PROXY = False

if os.environ.get('SOLITUDE_PROXY', 'disabled') == 'enabled':
    raise ValueError('You have the environment variable SOLITUDE_PROXY set to '
                     '"enabled", this breaks the tests, aborting.')

PAYPAL_PROXY = False
PAYPAL_URLS_ALLOWED = ('https://marketplace-dev.allizom.org',)

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

# We don't want to hit the live servers in tests.
BANGO_MOCK = True
ZIPPY_MOCK = True
BOKU_MOCK = True

SITE_URL = 'http://localhost/'

SEND_USER_ID_TO_BANGO = True
CHECK_BANGO_TOKEN = True

REQUIRE_OAUTH = False

# Suds keeps a cache of the WSDL around, so after completing the test run,
# lets remove that so it doesn't affect the next test run.
def _cleanup():
    target = os.path.join(gettempdir(), 'suds')
    if os.path.exists(target):
        shutil.rmtree(target)

atexit.register(_cleanup)
