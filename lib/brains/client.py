from urlparse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import braintree
from django_statsd.clients import statsd

from solitude.logger import getLogger

log = getLogger('s.brains')


class AuthEnvironment(braintree.environment.Environment):

    def __init__(self, real):
        self._url = urlparse(settings.BRAINTREE_PROXY)
        self._real = real

        super(self.__class__, self).__init__(
            self._url.hostname, self._url.port, '',
            self._url.scheme == 'https', None)


AuthSandbox = AuthEnvironment(braintree.environment.Environment.Sandbox)
AuthProduction = AuthEnvironment(braintree.environment.Environment.Production)


class Http(braintree.util.http.Http):

    def http_do(self, verb, path, headers, body):
        # Tell solitude-auth where we really want this request to go to.
        headers['x-solitude-service'] = self.environment._real.base_url + path
        # Set the URL of the request to point to the auth server.
        path = self.environment._url.path

        with statsd.timer('solitude.braintree.api'):
            status, text = super(Http, self).http_do(verb, path, headers, body)
        statsd.incr('solitude.braintree.response.{0}'.format(status))
        return status, text


def get_client():
    """
    Use this to get the right client and communicate with Braintree.
    """
    environments = {
        'sandbox': AuthSandbox,
        'production': AuthProduction,
    }

    if not settings.BRAINTREE_MERCHANT_ID:
        raise ImproperlyConfigured('BRAINTREE_MERCHANT_ID must be set.')

    braintree.Configuration.configure(
        environments[settings.BRAINTREE_ENVIRONMENT],
        settings.BRAINTREE_MERCHANT_ID,
        'public key added by solitude-auth',
        'private key added by solitude-auth',
        http_strategy=Http
    )
    return braintree
