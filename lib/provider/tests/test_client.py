from django.test import TestCase

from nose.tools import eq_, ok_

from ..client import get_client, Client, ClientProxy


class TestClientObj(TestCase):

    def test_non_existant(self):
        client = Client('does-not-exist')
        eq_(client.api, None)

    def test_existing(self):
        config = {
            'bob': {
                'url': 'http://f.com',
                'auth': {'key': 'k', 'secret': 's'}
                }
            }

        with self.settings(ZIPPY_CONFIGURATION=config):
            client = Client('bob')
            ok_(client.api)
            eq_(client.config, config['bob'])

    def test_proxy(self):
        with self.settings(ZIPPY_MOCK=False, ZIPPY_PROXY='http://blah/proxy'):
            client = get_client('bob')
            ok_(isinstance(client, ClientProxy))
            eq_(client.api._store['base_url'], 'http://blah/proxy/bob')
