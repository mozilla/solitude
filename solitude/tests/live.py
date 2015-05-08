
from django.test import LiveServerTestCase
from django.test.utils import override_settings

from nose.plugins.attrib import attr

from curling import lib
from solitude.base import getLogger

log = getLogger('s.tests')

configs = {
    'REQUIRE_OAUTH': True,
    'SITE_URL': 'http://localhost:8081',
    'CLIENT_OAUTH_KEYS': {'foo': 'bar'},
    'DEBUG': False,
    'DEBUG_PROPAGATE_EXCEPTIONS': False,
}


@attr('live')
@override_settings(**configs)
class LiveTestCase(LiveServerTestCase):

    @property
    def request(self):
        api = lib.API(self.live_server_url)
        api.activate_oauth(*configs['CLIENT_OAUTH_KEYS'].items()[0])
        return api
