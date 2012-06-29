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

# PayPal values.
PAYPAL_APP_ID = ''
PAYPAL_AUTH = {'USER': '', 'PASSWORD': '', 'SIGNATURE': ''}
PAYPAL_CHAINS = ()
PAYPAL_CERT = None
PAYPAL_LIMIT_PREAPPROVAL = True
PAYPAL_URL_WHITELIST = ()
PAYPAL_USE_SANDBOX = True
