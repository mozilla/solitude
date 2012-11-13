# test_utils picks this file up for testing.
import os
from solitude.settings.base import *

filename = os.path.join(os.path.dirname(__file__), 'sample.key')

AES_KEYS = {
    'buyerpaypal:key': filename,
    'sellerpaypal:id': filename,
    'sellerpaypal:token': filename,
    'sellerpaypal:secret': filename,
    'sellerbluevia:id': filename,
    'sellerproduct:secret': filename,
}

SOLITUDE_PROXY = False

PAYPAL_MOCK = False
PAYPAL_PROXY = False
PAYPAL_URL_WHITELIST = ('https://marketplace-dev.allizom.org',)

# How tastypie processes error depends upon these settings.
DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
TASTYPIE_FULL_DEBUG = DEBUG

DUMP_REQUESTS = False

HMAC_KEYS = {'2011-01-01': 'cheesecake'}
from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)

BANGO_EXPORTER_WSDL = 'https://nowhere/mozillaexporter/?WSDL'
BANGO_BILLING_CONFIG_WSDL = 'https://nowhere/billingconfiguration/?WSDL'
