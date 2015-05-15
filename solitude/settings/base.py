import logging.handlers
import os
from decimal import Decimal
from urlparse import urlparse

from django.core.urlresolvers import reverse_lazy

import cef

import dj_database_url


host = os.environ.get('SOLITUDE_URL', 'http://localhost:2602')

####################################################
# Django settings.
#
# See https://docs.djangoproject.com/en/dev/ref/settings/ for info.
#
ALLOWED_HOSTS = []

SOLITUDE_PROXY = os.environ.get('SOLITUDE_PROXY', 'disabled') == 'enabled'

if SOLITUDE_PROXY:
    DATABASES = {'default': {}}
else:
    db_env = ''
    envs = ['SOLITUDE_DATABASE', 'DATABASE_URL']
    for env in envs:
        if os.environ.get(env):
            db_env = env
            break

    # Solitude will use the first environment variable it can find.
    DATABASES = {
        'default': dj_database_url.config(
            default='mysql://root:@localhost:3306/solitude',
            env=db_env)
    }

if 'mysql' in DATABASES['default'].get('ENGINE', ''):
    opt = DATABASES['default'].get('OPTIONS', {})
    opt['init_command'] = 'SET storage_engine=InnoDB'
    opt['charset'] = 'utf8'
    opt['use_unicode'] = True
    DATABASES['default']['OPTIONS'] = opt
DATABASES['default']['TEST_CHARSET'] = 'utf8'
DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'

DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True

HMAC_KEYS = {
    '2011-01-01': 'please change me',
}

INSTALLED_APPS = (
    'aesfield',
    'django_extensions',
    'django_nose',
    'django_statsd',
    'solitude',
    'rest_framework',
    'django_filters'
)

LOCALE_PATHS = ()

base_fmt = ('%(name)s:%(levelname)s %(message)s '
            ':%(pathname)s:%(lineno)s')
error_fmt = ('%(name)s:%(levelname)s %(request_path)s %(message)s '
             ':%(pathname)s:%(lineno)s')

LOGGING = {
    'version': 1,
    'filters': {},
    'formatters': {
        'solitude': {
            '()': 'solitude.logger.SolitudeFormatter',
            'format':
                '%(name)s:%(levelname)s '
                '%(OAUTH_KEY)s:%(TRANSACTION_ID)s '
                '%(message)s :%(pathname)s:%(lineno)s'
        },
        'cef': {
            '()': cef.SysLogFormatter,
            'datefmt': '%H:%M:%s',
        }
    },
    'handlers': {
        'unicodesyslog': {
            '()': 'mozilla_logger.log.UnicodeHandler',
            'facility': logging.handlers.SysLogHandler.LOG_LOCAL7,
            'formatter': 'solitude',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
        },
        'console': {
            '()': logging.StreamHandler,
            'formatter': 'solitude',
        },
        'cef_syslog': {
            '()': logging.handlers.SysLogHandler,
            'facility': logging.handlers.SysLogHandler.LOG_LOCAL4,
            'formatter': 'cef',
        },

    },
    'loggers': {
        '': {
            'handlers': ['unicodesyslog', 'sentry'],
            'level': 'INFO',
            'propagate': True
        },
        's.brains.management': {
            'handlers': ['unicodesyslog', 'console'],
            'level': 'INFO',
            'propagate': True
        },
        's.auth': {
            'level': 'INFO',
        },
        's.services': {
            'handlers': ['unicodesyslog'],
            'level': 'ERROR',
        },
        'django.request': {
            'handlers': ['unicodesyslog', 'sentry'],
            'level': 'INFO',
            'propagate': True
        },
        'requests.packages.urllib3.connectionpool': {
            'level': 'WARNING',
            'propagate': True
        },
        'suds': {
            # This is very verbose and setting it to DEBUG may
            # cause problems on jenkins because the logging within suds
            # actually causes errors.
            'level': 'ERROR',
            'propagate': True
        },
        'boto': {
            'level': 'ERROR',
            'propagate': True
        },
        'cef': {
            'handlers': ['cef_syslog']
        },
        'newrelic': {
            'level': 'ERROR'
        },
        # With no-one monitoring this, it really has become pretty useless,
        # so lets leave the code there, but not fill up our logs.
        'paranoia': {
            'level': 'ERROR'
        }
    }
}
LOGGING_CONFIG = 'django.utils.log.dictConfig'

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
ROOT_URLCONF = 'solitude.urls'

SECRET_KEY = 'please change this'
SENSITIVE_DATA_KEYS = ['bankAccountNumber', 'pin', 'secret']

# Remove traces of jinja and jingo from solitude.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

USE_I18N = False
USE_L10N = False
USE_ETAGS = True

####################################################
# Project settings.
#
# These are the AES encryption keys for different fields.
AES_KEYS = {
    'buyeremail:key': 'solitude/settings/sample.key',
    'sellerproduct:secret': 'solitude/settings/sample.key',
    'bango:signature': 'solitude/settings/sample.key',
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

# Set up bcrypt.
HMAC_KEYS = {
    '2011-01-01': 'please change me',
}
from django_sha2 import get_password_hashers
PASSWORD_HASHERS = get_password_hashers(BASE_PASSWORD_HASHERS, HMAC_KEYS)

# Access the cleansed settings values.
CLEANSED_SETTINGS_ACCESS = False

# A mapping of the keys and secrets that will be used to sign OAuth
# for any server talking to this server. Is not used if REQUIRE_OAUTH is False.
CLIENT_OAUTH_KEYS = {
    'marketplace': 'please change this',
    'webpay': 'please change this',
    'payments-service': 'please change this',
    'local-curling-client': 'please change this',
}

# Paranoia levels.
DJANGO_PARANOIA_REPORTERS = [
    'django_paranoia.reporters.log',
    'django_paranoia.reporters.cef_'
]

# Prints out incoming and outgoing HTTP Requests.
DUMP_REQUESTS = False

# Remove traces of jinja and jingo from solitude.
JINJA_CONFIG = lambda: ''

MINIFY_BUNDLES = {}

# New Relic is configured here.
NEWRELIC_INI = None

# The number of PIN failures before we lock them out.
PIN_FAILURES = 5

# The amount of time before you can try it again in seconds.
PIN_FAILURE_LENGTH = 300

PROJECT_MODULE = 'solitude'

# If this flag is set, any communication will require OAuth signing of the
# request. Without this, OAuth is optional. This should be True for production.
REQUIRE_OAUTH = True

# URLs that should not require oauth autentication, for example Nagios checks.
SKIP_OAUTH = (reverse_lazy('services.status'),)

if SOLITUDE_PROXY:
    # The proxy runs with no database access. And just a couple of libraries.
    INSTALLED_APPS += (
        'lib.proxy',
    )
    MIDDLEWARE_CLASSES = (
        'solitude.middleware.LoggerMiddleware',
        'django_statsd.middleware.GraphiteMiddleware',
    )
else:
    # If this is the full solitude instance add in the rest.
    INSTALLED_APPS += (
        'lib.buyers',
        'lib.sellers',
        'lib.transactions',
        'lib.bango',
        'lib.brains'
    )
    MIDDLEWARE_CLASSES = (
        'solitude.middleware.LoggerMiddleware',
        'django.middleware.transaction.TransactionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.http.ConditionalGetMiddleware',
        'django_statsd.middleware.GraphiteMiddleware',
        'django_paranoia.middleware.Middleware'
    )

STATSD_CLIENT = 'django_statsd.clients.normal'

# Time in seconds that a transaction expires. If you try to complete a
# transaction after this time, it will fail.
TRANSACTION_EXPIRY = 60 * 30

# Time in seconds after a transaction is created that it becomes locked.
# After that time, no changes can be made to a transaction.
TRANSACTION_LOCKDOWN = 60 * 60 * 24

# Ensure that sensitive data in the JSON is filtered out.
RAVEN_CONFIG = {
    'processors': ('solitude.processor.JSONProcessor',),
}

REST_FRAMEWORK = {
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'solitude.authentication.RestOAuthAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_SERIALIZER_CLASS':
        'solitude.paginator.CustomPaginationSerializer',
    'DEFAULT_FILTER_BACKENDS': (
        'solitude.filter.StrictQueryFilter',
    ),
    'EXCEPTION_HANDLER': 'solitude.exceptions.custom_exception_handler',
    'PAGINATE_BY': 20,
    'PAGINATE_BY_PARAM': 'limit'
}


# For uploading logs from the server.
S3_AUTH = {'key': '',
           'secret': ''}
S3_BUCKET = ''

# We don't actually use session cookies at all in solitude. So its safe
# to set this, to stop funfactory complaining about it.
SESSION_COOKIE_SECURE = True

# Set this for OAuth.
SITE_URL = host

# This is overridden on servers to ensure it goes to the right place.
SYSLOG_TAG = 'solitude'

# Configure our test runner for some nice test output.
NOSE_PLUGINS = [
    'nosenicedots.NiceDots',
    'blockage.plugins.NoseBlockage',
]

NOSE_ARGS = [
    '--logging-clear-handlers',
    '--logging-filter=xsd',
    '--with-nicedots',
    '--with-blockage',
]

# Figure out which tests we run. By default that's no live tests.
# LIVE_TESTS=live,braintree  < runs tests marked as live and braintree
tests = os.environ.get('LIVE_TESTS', '')

if not tests:
    # If you specified no tests, exclude them all by default.
    NOSE_ARGS.append('-a !{0}'.format(',!'.join(['live', 'braintree'])))
else:
    # If you specified something, just pass it through.
    NOSE_ARGS.append('-a ' + tests)

# Figure out the whitelist.
http = []
# Split tests to distinguish between !live and live etc.
if 'live' in tests.split(','):
    http.append('localhost')
if 'braintree' in tests.split(','):
    http.append('api.sandbox.braintreegateway.com')

NOSE_ARGS.append('--http-whitelist=' + ','.join(http))

# Below is configuration of payment providers.

###############################################################################
# Start PayPal settings.
#
PAYPAL_APP_ID = ''
PAYPAL_AUTH = {'USER': '', 'PASSWORD': '', 'SIGNATURE': ''}
PAYPAL_CERT = None
PAYPAL_CHAINS = ()
PAYPAL_LIMIT_PREAPPROVAL = True
PAYPAL_MOCK = False
PAYPAL_PROXY = ''
PAYPAL_URLS_ALLOWED = ()
PAYPAL_USE_SANDBOX = True

###############################################################################
# Start Bango settings.

# If you want to just run a mock, that will get you so far.
BANGO_MOCK = False

# These are the credentials for calling Bango.
BANGO_AUTH = {'USER': 'Mozilla', 'PASSWORD': ''}

# Fake out refunds, set this to True for test until bug 845332 is resolved.
# Turning this on, just fakes out the Bango backend completely and never
# really refunds anything.
#
# This is different from manual refund which is to force a refund through
# if Bango use the manual refund flow.
BANGO_FAKE_REFUNDS = True

# When True, send product icon URLs to Bango in the billing config task.
BANGO_ICON_URLS = True

# When True, send MOZ_USER_ID to Bango in the billing config task.
SEND_USER_ID_TO_BANGO = True

# Time in seconds after which a Bango API request will be aborted.
# We can deal with slow requests because we mostly use background tasks.
# The API can indeed be slow, see bug 883389.
BANGO_TIMEOUT = 30

# Time in days after which Bango statuses will be cleaned by the
# `clean_statuses` command.
BANGO_STATUSES_LIFETIME = 30

# When True, use the token check service to verify query string parameters.
CHECK_BANGO_TOKEN = True

# The Bango API environment. This value must be an existing subdirectory
# under lib/bango/wsdl.
BANGO_ENV = 'test'

# If you'd like to use the internal Solitude proxy for Bango, set this to
# the value of the Solitude proxy instance.
BANGO_PROXY = os.getenv('SOLITUDE_BANGO_PROXY', '')

# Set this to a string if you'd like to insert data into the vendor
# and company name when a package is created.
BANGO_INSERT_STAGE = ''

# Notification end points use basic auth.
# These are the credentials for Bango calling us.
BANGO_BASIC_AUTH = {'USER': '', 'PASSWORD': ''}

# The URL that Bango will send notifications too. If this is not set, the
# notification URL will not be set.
BANGO_NOTIFICATION_URL = ''

# End Bango settings.
###############################################################################

###############################################################################
# Start Zippy settings.

# Mock out Zippy, because we are sharing zippy.paas configuration.
ZIPPY_MOCK = False

url = os.environ.get('ZIPPY_BASE_URL', 'https://zippy.paas.allizom.org')

# Override this to configure some zippy backends.
ZIPPY_CONFIGURATION = {
    'reference': {
        # No trailing slash.
        'url': url,
        'auth': {
            'key': 'zippy-on-paas',
            'secret':
                'sjahgfjdrtgdargalrgadlfghadfjgadrgarfgnadfgdfagadflhdafg',
            'realm': urlparse(url).netloc
        },
    },
}

# The URL for a solitude proxy to zippy.
ZIPPY_PROXY = os.getenv('SOLITUDE_ZIPPY_PROXY', '')

# End Zippy settings.
###############################################################################

###############################################################################
# Start Braintree settings.

# You'll find this in the Braintree account under:
# Account > My User > API keys.

# To make it easier, we'll pull these from the env as well.
BRAINTREE_MERCHANT_ID = os.getenv('BRAINTREE_MERCHANT_ID', '')
BRAINTREE_PUBLIC_KEY = os.getenv('BRAINTREE_PUBLIC_KEY', '')
BRAINTREE_PRIVATE_KEY = os.getenv('BRAINTREE_PRIVATE_KEY', '')

# See lib.brains.client for the options.
BRAINTREE_ENVIRONMENT = 'sandbox'

# Mock out Braintree. Overrides environment.
BRAINTREE_MOCK = False

# A definiton of Products for Payments for Firefox Accounts for Braintree.
BRAINTREE_CONFIG = {
    'concrete': {
        'seller': 'mozilla-concrete',
        'products': [
            {
                'name': 'brick',
                'amount': Decimal('10')
            },
            {
                'name': 'mortar',
                'amount': Decimal('5')
            }
        ]
    }
}
