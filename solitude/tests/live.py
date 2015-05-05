from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import LiveServerTestCase
from django.test.utils import override_settings

from nose.plugins.attrib import attr

from curling import lib
from solitude.base import getLogger

log = getLogger('s.tests')

configs = {
    'REQUIRE_OAUTH': True,
    'SITE_URL': 'http://localhost:8081',
    'CLIENT_OAUTH_KEYS': {'foo': 'bar'}
}


@attr('live')
@override_settings(**configs)
class LiveTestCase(LiveServerTestCase):

    def setUp(self):
        for key in ['BRAINTREE_MERCHANT_ID',
                    'BRAINTREE_PUBLIC_KEY',
                    'BRAINTREE_PRIVATE_KEY']:
            if not getattr(settings, key):
                raise ImproperlyConfigured('{0} is empty'.format(key))

        super(LiveTestCase, self).setUp()

    @property
    def request(self):
        api = lib.API(self.live_server_url)
        api.activate_oauth(*configs['CLIENT_OAUTH_KEYS'].items()[0])
        return api
