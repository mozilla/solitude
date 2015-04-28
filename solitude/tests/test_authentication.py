from django import test
from django.conf import settings
from django.test import RequestFactory

from curling.lib import HttpClientError
from mock import patch
from nose.tools import eq_, ok_, raises
from rest_framework.exceptions import AuthenticationFailed

from solitude.authentication import Consumer, RestOAuthAuthentication
from solitude.tests.live import LiveTestCase

keys = {'foo': 'bar'}
keys_dict = {'key': 'foo', 'secret': 'bar'}


@patch.object(settings, 'CLIENT_OAUTH_KEYS', keys)
class TestDRFAuthentication(test.TestCase):

    def setUp(self):
        self.authentication = RestOAuthAuthentication()
        self.factory = RequestFactory()
        self.consumer = Consumer(*keys.items()[0])

    def test_skip(self):
        req = self.factory.get('/skip-oauth/')
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=['/skip-oauth/']):
            ok_(self.authentication.authenticate(req))

    @raises(AuthenticationFailed)
    def test_not_skip(self):
        req = self.factory.get('/require-oauth/')
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=['/skip-oauth/']):
            eq_(self.authentication.authenticate(req))


class TestAuthentication(LiveTestCase):

    def test_valid_auth(self):
        ok_(self.request.by_url('/generic/transaction/').get())

    def test_invalid_auth(self):
        with self.settings(CLIENT_OAUTH_KEYS={'f': 'b'}):
            with self.assertRaises(HttpClientError) as err:
                self.request.by_url('/generic/transaction/').get()
            eq_(err.exception.response.status_code, 403)
