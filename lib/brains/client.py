from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import braintree
from django_statsd.clients import statsd

from lib.brains.errors import MockError
from lib.brains.tests.samples import get_sample
from solitude.logger import getLogger

log = getLogger('s.brains')

# Call set_mocks in the tests to populate this value.
mocks = []


def set_mocks(*args):
    global mocks
    mocks = []
    for verb, url, status, filename in list(reversed(args)):
        # Between the double slash is where the BRAINTREE_MERCHANT_ID
        # goes. In tests this will be blank, hence the double slash.
        mocks.append((verb, '/merchants//' + url, status,
                      get_sample(filename) if filename else ''))


class Http(braintree.util.http.Http):

    def http_do(self, *args, **kw):
        with statsd.timer('solitude.braintree.api'):
            status, text = super(Http, self).http_do(*args, **kw)
        statsd.incr('solitude.braintree.response.{0}'.format(status))
        return status, text


class HttpMock(Http):

    def http_do(self, http_verb, full_path, headers, body):
        try:
            next_mock = mocks.pop()
            if next_mock[:2] != (http_verb, full_path):
                # The mock was called in an order you didn't expect.
                raise MockError(
                    'Mock called in wrong order, expecting: {0} {1}'
                    .format(http_verb, full_path))
            return next_mock[2:]
        except KeyError:
            raise MockError(
                'No mock exists for: {0} {1}'
                .format(http_verb, full_path))


def get_client():
    """
    Use this to get the right client and communicate with Braintree.
    """
    strategy = Http
    if settings.BRAINTREE_MOCK:
        log.warning('Braintree is using the mock client')
        strategy = HttpMock

    elif not settings.BRAINTREE_PRIVATE_KEY:
        raise ImproperlyConfigured('BRAINTREE_PRIVATE_KEY is blank, configure '
                                   'your braintree settings.')

    environments = {
        'sandbox': braintree.Environment.Sandbox,
        'production': braintree.Environment.Production,
    }

    braintree.Configuration.configure(
        environments[settings.BRAINTREE_ENVIRONMENT],
        settings.BRAINTREE_MERCHANT_ID,
        settings.BRAINTREE_PUBLIC_KEY,
        settings.BRAINTREE_PRIVATE_KEY,
        http_strategy=strategy
    )
    return braintree
