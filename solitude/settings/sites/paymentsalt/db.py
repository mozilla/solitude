"""private_base will be populated from puppet and placed in this directory"""

import logging

import dj_database_url

import private_base as private

from solitude.settings import base
from django_sha2 import get_password_hashers


ADMINS = ()
ALLOWED_HOSTS = ['*']

DATABASES = {}
DATABASES['default'] = dj_database_url.parse(private.DATABASES_DEFAULT_URL)
DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
DATABASES['default']['OPTIONS'] = {'init_command': 'SET storage_engine=InnoDB'}

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

SYSLOG_TAG = 'http_app_payments_paymentsalt'
TEMPLATE_DEBUG = DEBUG

# Solitude specific settings.
AES_KEYS = private.AES_KEYS
CLIENT_OAUTH_KEYS = private.CLIENT_OAUTH_KEYS

NEWRELIC_INI = '/etc/newrelic.d/payments-alt.allizom.org.ini'

SITE_URL = 'https://payments-alt-solitude.allizom.org'

S3_AUTH = {'key': private.S3_AUTH_KEY, 'secret': private.S3_AUTH_SECRET}
S3_BUCKET = private.S3_BUCKET

REQUIRE_OAUTH = True

PAYPAL_PROXY = private.PAYPAL_PROXY
PAYPAL_URL_WHITELIST = ('https://payments-alt.allizom.org',)

BANGO_BASIC_AUTH = private.BANGO_BASIC_AUTH
BANGO_ENV = 'prod'
BANGO_INSERT_STAGE = 'FROM STAGE '
BANGO_PROXY = private.BANGO_PROXY
BANGO_NOTIFICATION_URL = (
    'https://payments-alt.allizom.org/mozpay/bango/notification')

ZIPPY_PROXY = 'https://payments-alt-solitude-proxy.allizom.org/proxy/provider'
ZIPPY_CONFIGURATION = {
    'boku': {
        'url': base.BOKU_API_DOMAIN
    }
}

BOKU_PROXY = ZIPPY_PROXY
