"""private_base will be populated from puppet and placed in this directory"""

import logging

import private_base as private

from solitude.settings import base
from django_sha2 import get_password_hashers


ADMINS = ()
ALLOWED_HOSTS = ['payments-proxy-dev.allizom.org']

DATABASES = {'default': {}}

DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = False

HMAC_KEYS = private.HMAC_KEYS

PASSWORD_HASHERS = get_password_hashers(base.BASE_PASSWORD_HASHERS, HMAC_KEYS)

LOG_LEVEL = logging.DEBUG

SECRET_KEY = private.SECRET_KEY

SENTRY_DSN = private.SENTRY_DSN

STATSD_HOST = private.STATSD_HOST
STATSD_PORT = private.STATSD_PORT
STATSD_PREFIX = private.STATSD_PREFIX

SYSLOG_TAG = 'http_app_payments_dev'
TEMPLATE_DEBUG = DEBUG

# Solitude specific settings.
AES_KEYS = {}

CLEANSED_SETTINGS_ACCESS = True
CLIENT_JWT_KEYS = private.CLIENT_JWT_KEYS

NEWRELIC_INI = '/etc/newrelic.d/payments-proxy-dev.allizom.org.ini'

# Below is configuration of payment providers.

PAYPAL_APP_ID = private.PAYPAL_APP_ID
PAYPAL_AUTH = private.PAYPAL_AUTH
PAYPAL_CHAINS = private.PAYPAL_CHAINS
PAYPAL_URL_WHITELIST = ('https://marketplace-dev.allizom.org',)
PAYPAL_USE_SANDBOX = True

BANGO_ENV = 'test'
BANGO_AUTH = private.BANGO_AUTH

ZIPPY_CONFIGURATION = {
    'reference': {
        'url': 'https://zippy.paas.allizom.org',
        'auth': {'key': private.ZIPPY_PAAS_KEY,
                 'secret': private.ZIPPY_PAAS_SECRET,
                 'realm': 'zippy.paas.allizom.org'}
    },
    'boku': {
        'url': base.BOKU_API_DOMAIN,
    }
}
