from nose.tools import eq_, ok_
from test_utils import TestCase

from ..client import Client


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
