import dj_database_url
import logging.handlers
import os
import urlparse

from funfactory.settings_base import *

PROJECT_MODULE = 'solitude'
MINIFY_BUNDLES = {}

# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = (
    'aesfield',
    'funfactory',
    'django_nose',
    'django_statsd',
    'djcelery',
    'solitude',
)
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config()
    }
    if 'mysql' in DATABASES['default']['ENGINE']:
        opt = DATABASES['default'].get('OPTIONS', {})
        opt['init_command'] = 'SET storage_engine=InnoDB'
        opt['charset'] = 'utf8'
        opt['use_unicode'] = True
        DATABASES['default']['OPTIONS'] = opt
    DATABASES['default']['TEST_CHARSET'] = 'utf8'
    DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'
else:
    DATABASES = {}


LOCALE_PATHS = ()
USE_I18N = False
USE_L10N = False

SOLITUDE_PROXY = os.environ.get('SOLITUDE_PROXY', 'disabled') == 'enabled'
if SOLITUDE_PROXY:
    # The proxy runs with no database access. And just a couple of libraries.
    INSTALLED_APPS += (
        'lib.proxy',
    )
else:
    # If this is the full solitude instance add in the rest.
    INSTALLED_APPS += (
        'lib.buyers',
        'lib.sellers',
        'lib.transactions',
        'lib.delayable'
    )

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

# Remove traces of jinja and jingo from solitude.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
JINJA_CONFIG = lambda: ''

if not SOLITUDE_PROXY:
    MIDDLEWARE_CLASSES = (
        'django.middleware.transaction.TransactionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django_statsd.middleware.GraphiteMiddleware',
        'django_statsd.middleware.TastyPieRequestTimingMiddleware',
        'django_paranoia.middleware.Middleware'
    )
else:
    MIDDLEWARE_CLASSES = (
        'django_statsd.middleware.GraphiteMiddleware',
    )

SESSION_COOKIE_SECURE = True

STATSD_CLIENT = 'django_statsd.clients.normal'

# PayPal values.
PAYPAL_APP_ID = ''
PAYPAL_AUTH = {'USER': '', 'PASSWORD': '', 'SIGNATURE': ''}
PAYPAL_CHAINS = ()
PAYPAL_CERT = None
PAYPAL_LIMIT_PREAPPROVAL = True
PAYPAL_URL_WHITELIST = ()
PAYPAL_USE_SANDBOX = True
PAYPAL_PROXY = ''
PAYPAL_MOCK = False

# Access the cleansed settings values.
CLEANSED_SETTINGS_ACCESS = False
# The status object for tastypie services.
SERVICES_STATUS_MODULE = 'lib.services.resources'

LOGGING = {
    'filters': {},
    'formatters': {},
    'handlers': {
        'unicodesyslog': {
            '()': 'solitude.settings.log.UnicodeHandler',
            'facility': logging.handlers.SysLogHandler.LOG_LOCAL7,
            'formatter': 'prod',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
    },
    'loggers': {
        's': {
            'handlers': ['unicodesyslog', 'console'],
            'level': 'INFO',
        },
        'suds': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'sentry.errors': {
            'handlers': ['unicodesyslog'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['unicodesyslog', 'sentry'],
            'level': 'INFO',
        },
    },
}

# These are the AES encryption keys for different fields.
AES_KEYS = {
    'buyerpaypal:key': '',
    'sellerpaypal:id': '',
    'sellerpaypal:token': '',
    'sellerpaypal:secret': '',
    'sellerproduct:secret': '',
}

# Playdoh ships with sha512 password hashing by default. Bcrypt+HMAC is safer,
# so it is recommended. Please read
# <https://github.com/fwenzel/django-sha2#readme>, uncomment the bcrypt hasher
# and pick a secret HMAC key for your application.
BASE_PASSWORD_HASHERS = (
    'django_sha2.hashers.BcryptHMACCombinedPasswordVerifier',
    'django_sha2.hashers.SHA512PasswordHasher',
    'django_sha2.hashers.SHA256PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
)

DUMP_REQUESTS = False

# If this flag is set, any communication will require JWT encoding of the
# data using a key set in CLIENT_JWT_KEYS. Note: this does not require JWT for
# all things, eg: nagios checks.
REQUIRE_JWT = False

# A mapping of the keys and secrets that will be used to encode the JWT
# for any server talking to this server.
CLIENT_JWT_KEYS = {}

# Bango API settings.
BANGO_AUTH = {'USER': 'Mozilla', 'PASSWORD': ''}
# The Bango API environment. This value must be an existing subdirectory
# under lib/bango/wsdl.
BANGO_ENV = 'test'
BANGO_MOCK = False
BANGO_PROXY = ''

# Time in seconds that a transaction expires. If you try to complete a
# transaction after this time, it will fail.
TRANSACTION_EXPIRY = 60 * 30

# Celery configs.
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_IGNORE_RESULT = False
CELERY_IMPORTS = ('lib.delayable.tasks',)
CELERY_RESULT_BACKEND = 'database'
CELERYD_HIJACK_ROOT_LOGGER = False

# Paranoia levels.
DJANGO_PARANOIA_REPORTERS = [
    'django_paranoia.reporters.log',
    'django_paranoia.reporters.cef_'
]

# The number of PIN failures before we lock them out.
PIN_FAILURES = 5
# The amount of time before you can try it again in seconds.
PIN_FAILURE_LENGTH = 600
