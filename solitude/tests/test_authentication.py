from django import test
from django.conf import settings
from django.test import RequestFactory

from mock import patch
from nose.tools import eq_, ok_
from rest_framework.exceptions import AuthenticationFailed

from solitude.authentication import Consumer, RestOAuthAuthentication

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

    def test_not_skip(self):
        req = self.factory.get('/require-oauth/')
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=['/skip-oauth/']):
            eq_(self.authentication.authenticate(req), AuthenticationFailed)
