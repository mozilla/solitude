from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import braintree
from django_statsd.clients import statsd

from lib.brains.errors import MissingMockError
from lib.brains.tests.samples import get_sample
from solitude.logger import getLogger

log = getLogger('s.brains')

mocks = {
    'GET /merchants//customers/does-not-exist': (404, ''),
    'GET /merchants//customers/minimal': (200, get_sample('customer-minimal')),
    'GET /merchants//customers/full': (200, get_sample('customer-full')),
}


class Http(braintree.util.http.Http):

    def http_do(self, *args, **kw):
        with statsd.timer('solitude.braintree.api'):
            status, text = super(Http, self).http_do(*args, **kw)
        statsd.incr('solitude.braintree.response.{0}'.format(status))
        return status, text


class HttpMock(Http):

    def http_do(self, http_verb, full_path, headers, body):
        try:
            return mocks['{0} {1}'.format(http_verb, full_path)]
        except KeyError:
            raise MissingMockError(
                'No mock exists for verb: {0} and path: {1}.'
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
