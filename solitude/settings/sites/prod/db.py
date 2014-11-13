"""private_base will be populated from puppet and placed in this directory"""

import logging

import dj_database_url

import private_base as private

from solitude.settings import base
from django_sha2 import get_password_hashers

ADMINS = ()
ALLOWED_HOSTS = ('*',)

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

SYSLOG_TAG = 'http_app_payments'
TEMPLATE_DEBUG = DEBUG

# Solitude specific settings.
AES_KEYS = private.AES_KEYS

CLIENT_OAUTH_KEYS = private.CLIENT_OAUTH_KEYS

REQUIRE_OAUTH = True

SITE_URL = 'https://payments.firefox.com'

S3_AUTH = {'key': private.S3_AUTH_KEY, 'secret': private.S3_AUTH_SECRET}
S3_BUCKET = private.S3_BUCKET

# Below is configuration of payment providers.

ZIPPY_CONFIGURATION = {}

PAYPAL_PROXY = private.PAYPAL_PROXY
PAYPAL_URL_WHITELIST = ('https://marketplace.firefox.com',)

BANGO_BASIC_AUTH = private.BANGO_BASIC_AUTH
BANGO_BILLING_CONFIG_V2 = True
BANGO_ENV = 'prod'
BANGO_FAKE_REFUNDS = False
BANGO_PROXY = private.BANGO_PROXY
BANGO_NOTIFICATION_URL = (
    'https://marketplace.firefox.com/mozpay/bango/notification')

NOSE_PLUGINS = []
