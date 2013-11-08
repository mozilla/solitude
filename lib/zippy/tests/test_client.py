from django.conf import settings

from nose import SkipTest
from nose.tools import eq_, ok_
from test_utils import TestCase

from ..client import Client, get_client


class TestClient(TestCase):

    def setUp(self):
        self.api = get_client('reference').api

    def test_seller_lifecycle(self):
        if settings.ZIPPY_MOCK:
            # That test is intended to be run against a real instance of Zippy.
            raise SkipTest
        res = self.api.sellers.get()
        eq_(res, [])
        seller = {
            'uuid': 'zippy-uuid',
            'status': 'ACTIVE',
            'name': 'John',
            'email': 'jdoe@example.org',
        }
        res = self.api.sellers.post(seller)
        seller.update({
            'resource_pk': '1',
            'resource_uri': '/sellers/1',
            })
        eq_(res, seller)
        res = self.api.sellers.get()
        eq_(res, [seller])
        res = self.api.sellers(seller['uuid']).get()
        eq_(res, seller)
        new_name = 'Jack'
        res = self.api.sellers(seller['uuid']).put({'name': new_name})
        seller.update({ 'name': new_name })
        eq_(res, seller)
        res = self.api.sellers(seller['uuid']).get()
        eq_(res, seller)
        res = self.api.sellers(seller['uuid']).delete()
        eq_(res, True)
        res = self.api.sellers.get()
        eq_(res, [])


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
