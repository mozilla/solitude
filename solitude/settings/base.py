# This is our very stripped down settings, we have no UI, no admin nothin'.
from funfactory.settings_base import *

PROJECT_MODULE = 'solitude'
MINIFY_BUNDLES = {}

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = (
    'aesfield',
    'funfactory',
    'django_nose',
    'lib.buyers',
    'lib.sellers',
    'lib.transactions',
    'solitude'
)

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

MIDDLEWARE_CLASSES = (
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.common.CommonMiddleware'
)

SESSION_COOKIE_SECURE = True

# PayPal values.
PAYPAL_APP_ID = ''
PAYPAL_AUTH = {'USER': '', 'PASSWORD': '', 'SIGNATURE': ''}
PAYPAL_CHAINS = ()
PAYPAL_CERT = None
PAYPAL_LIMIT_PREAPPROVAL = True
PAYPAL_URL_WHITELIST = ()
PAYPAL_USE_SANDBOX = True

# Access the cleansed settings values.
CLEANSED_SETTINGS_ACCESS = False

import logging.handlers

LOGGING = {
    'handlers': {
        'unicodesyslog': {
            '()': 'solitude.settings.log.UnicodeHandler',
            'facility': logging.handlers.SysLogHandler.LOG_LOCAL7,
            'formatter': 'prod',
        },
    },
    'loggers': {
        's': {
            'handlers': ['unicodesyslog'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['unicodesyslog'],
            'level': 'INFO',
        },
        'django.request.tastypie': {
            'handlers': ['unicodesyslog'],
            'level': 'INFO',
        },
    },
}

# This where we'll override the values.
AES_KEYS = {}
