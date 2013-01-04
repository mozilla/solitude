"""private_base will be populated from puppet and placed in this directory"""

import logging

import private_base as private


ADMINS = ()

DATABASES = {'default': {}}

DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = False

HMAC_KEYS = private.HMAC_KEYS

LOG_LEVEL = logging.DEBUG

SECRET_KEY = private.SECRET_KEY

SENTRY_DSN = private.SENTRY_DSN

STATSD_HOST = private.STATSD_HOST
STATSD_PORT = private.STATSD_PORT
STATSD_PREFIX = private.STATSD_PREFIX

SYSLOG_TAG = 'http_app_payments'
TEMPLATE_DEBUG = DEBUG

# Solitude specific settings.
AES_KEYS = {}

CLEANSED_SETTINGS_ACCESS = True
CLIENT_JWT_KEYS = private.CLIENT_JWT_KEYS

PAYPAL_APP_ID = private.PAYPAL_APP_ID
PAYPAL_AUTH = private.PAYPAL_AUTH
PAYPAL_CHAINS = private.PAYPAL_CHAINS
PAYPAL_URL_WHITELIST = ('https://marketplace.firefox.com',)
PAYPAL_USE_SANDBOX = True

BANGO_ENV = 'test'
BANGO_AUTH = private.BANGO_AUTH
