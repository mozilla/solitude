from django.conf import settings
from django.test import RequestFactory

from django import test
from curling.lib import sign_request
from mock import patch
from nose.tools import eq_, ok_
from rest_framework.exceptions import AuthenticationFailed

from solitude.authentication import (Consumer, OAuthAuthentication,
                                     RestOAuthAuthentication)

keys = {'foo': 'bar'}
keys_dict = {'key': 'foo', 'secret': 'bar'}


@patch.object(settings, 'CLIENT_OAUTH_KEYS', keys)
class TestAuthentication(test.TestCase):

    def setUp(self):
        self.authentication = OAuthAuthentication('api')
        self.factory = RequestFactory()
        self.consumer = Consumer(*keys.items()[0])

    def test_not_required(self):
        req = self.factory.get('/')
        with self.settings(REQUIRE_OAUTH=False, SKIP_OAUTH=[]):
            ok_(self.authentication.is_authenticated(req))

    def test_required(self):
        req = self.factory.get('/')
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=[]):
            ok_(not self.authentication.is_authenticated(req))

    def test_skip(self):
        req = self.factory.get('/skip-oauth/')
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=['/skip-oauth/']):
            ok_(self.authentication.is_authenticated(req))

    def test_not_skip(self):
        req = self.factory.get('/require-oauth/')
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=['/skip-oauth/']):
            ok_(not self.authentication.is_authenticated(req))

    def setup_authorization(self, keys):
        headers = {}
        sign_request(None, method='GET', extra=keys, headers=headers,
                     url=settings.SITE_URL)
        return headers['Authorization']

    def test_signed(self):
        authorization = self.setup_authorization(keys_dict)
        req = self.factory.get('/', HTTP_AUTHORIZATION=authorization)
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=[]):
            ok_(self.authentication.is_authenticated(req))
            eq_(req.OAUTH_KEY, 'foo')

    def test_signed_incorrectly(self):
        keys_ = keys_dict.copy()
        keys_['secret'] = 'baz'
        authorization = self.setup_authorization(keys_)
        req = self.factory.get('/foo/', HTTP_AUTHORIZATION=authorization)
        with self.settings(REQUIRE_OAUTH=True, SKIP_OAUTH=[]):
            ok_(not self.authentication.is_authenticated(req))
            eq_(req.OAUTH_KEY, None)


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
