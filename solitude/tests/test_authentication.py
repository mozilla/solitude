from django.conf import settings
from django.test import RequestFactory

import test_utils
from curling.lib import sign_request
from mock import patch
from nose.tools import eq_, ok_

from solitude.authentication import Consumer, OAuthAuthentication

keys = {'foo': 'bar'}
keys_dict = {'key': 'foo', 'secret': 'bar'}


@patch.object(settings, 'CLIENT_OAUTH_KEYS', keys)
class TestAuthentication(test_utils.TestCase):

    def setUp(self):
        self.authentication = OAuthAuthentication('api')
        self.factory = RequestFactory()
        self.consumer = Consumer(*keys.items()[0])

    def test_not_required(self):
        req = self.factory.get('/')
        with self.settings(REQUIRE_OAUTH=False):
            ok_(self.authentication.is_authenticated(req))

    def test_required(self):
        req = self.factory.get('/')
        with self.settings(REQUIRE_OAUTH=True):
            ok_(not self.authentication.is_authenticated(req))

    def test_signed(self):
        res = sign_request('GET', keys_dict, settings.SITE_URL, None)
        req = self.factory.get('/', HTTP_AUTHORIZATION=res)
        with self.settings(REQUIRE_OAUTH=True):
            ok_(self.authentication.is_authenticated(req))
            eq_(req.OAUTH_KEY, 'foo')

    def test_signed_incorrectly(self):
        keys_ = keys_dict.copy()
        keys_['secret'] = 'baz'
        res = sign_request('GET', keys_, settings.SITE_URL, None)
        req = self.factory.get('/foo/', HTTP_AUTHORIZATION=res)
        with self.settings(REQUIRE_OAUTH=True):
            ok_(not self.authentication.is_authenticated(req))
            eq_(req.OAUTH_KEY, None)
