from django.conf import settings

import braintree
from django_statsd.clients import statsd

from solitude.logger import getLogger

log = getLogger('s.brains')


class Http(braintree.util.http.Http):

    def http_do(self, *args, **kw):
        with statsd.timer('solitude.braintree.api'):
            status, text = super(Http, self).http_do(*args, **kw)
        statsd.incr('solitude.braintree.response.{0}'.format(status))
        return status, text


def get_client():
    """
    Use this to get the right client and communicate with Braintree.
    """
    environments = {
        'sandbox': braintree.Environment.Sandbox,
        'production': braintree.Environment.Production,
    }

    braintree.Configuration.configure(
        environments[settings.BRAINTREE_ENVIRONMENT],
        settings.BRAINTREE_MERCHANT_ID,
        settings.BRAINTREE_PUBLIC_KEY,
        settings.BRAINTREE_PRIVATE_KEY,
        http_strategy=Http
    )
    return braintree
