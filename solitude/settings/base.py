# This is our very stripped down settings, we have no UI, no admin nothin'.
import commonware.log
from funfactory.settings_base import *

PROJECT_MODULE = 'solitude'
MINIFY_BUNDLES = {}

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = (
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

# Logging stuff.
SYSLOG_TAG = 'http_app_solitude'
base_fmt = ('%(name)s:%(levelname)s %(message)s :%(pathname)s:%(lineno)s')

formatters = {
    'prod': {
        '()': commonware.log.Formatter,
        'datefmt': '%H:%M:%S',
        'format': ('%s: [%%(USERNAME)s][%%(REMOTE_ADDR)s] %s'
                   % (SYSLOG_TAG, base_fmt)),
    }
}

handlers = {
    'syslog': {
        'class': 'logging.handlers.SysLogHandler',
        'formatter': 'prod',
    }
}

loggers = {
    's': {
        'handlers': ['syslog'],
        'level': 'INFO',
    },
    'django.request': {
        'handlers': ['syslog'],
        'level': 'INFO',
    },
}

LOGGING = {
    'version': 1,
    'filters': {},
    'formatters': formatters,
    'handlers': handlers,
    'loggers': loggers,
}

# PayPal values.
PAYPAL_APP_ID = ''
PAYPAL_AUTH = {'USER': '', 'PASSWORD': '', 'SIGNATURE': ''}
PAYPAL_CHAINS = ()
PAYPAL_CERT = None
PAYPAL_LIMIT_PREAPPROVAL = True
PAYPAL_URL_WHITELIST = ()
PAYPAL_USE_SANDBOX = True
