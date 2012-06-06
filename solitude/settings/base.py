# This is our very stripped down settings, we have no UI, no admin nothin'.
from funfactory.settings_base import *

PROJECT_MODULE = 'solitude'
MINIFY_BUNDLES = {}

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = (
    'funfactory',
)

MIDDLEWARE_CLASSES = (
    'funfactory.middleware.LocaleURLMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.common.CommonMiddleware'
)

SESSION_COOKIE_SECURE = True
LOGGING = dict(loggers=dict(playdoh = {'level': logging.DEBUG}))
