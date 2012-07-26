# test_utils picks this file up for testing.
import os
filename = os.path.join(os.path.dirname(__file__),
                  'vendor-local/django-mysql-aesfield/aesfield/sample.key')
AES_KEYS = {
    'buyerpaypal:key': filename,
    'sellerpaypal:id': filename,
    'sellerpaypal:token': filename,
    'sellerpaypal:secret': filename,
    'sellerbluevia:id': filename,
}

PAYPAL_PROXY = False
PAYPAL_URL_WHITELIST = ('https://marketplace-dev.allizom.org',)

# How tastypie processes error depends upon these settings.
DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
TASTYPIE_FULL_DEBUG = DEBUG

DUMP_REQUESTS = False
