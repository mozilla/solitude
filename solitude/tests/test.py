import json

import jwt
import mock
from nose.tools import eq_
import simplejson
from tastypie.exceptions import ImmediateHttpResponse
import test_utils

from lib.paypal.errors import PaypalError
from solitude.base import APITest, JWTDecodeError, JWTSerializer, Resource


class TestError(test_utils.TestCase):

    def setUp(self):
        self.request = test_utils.RequestFactory().get('/')
        self.resource = Resource()

    def test_error(self):
        try:
            1/0
        except Exception as error:
            res = self.resource._handle_500(self.request, error)

        data = json.loads(res.content)
        eq_(data['error_code'], '')
        eq_(data['error_message'], 'integer division or modulo by zero')

    def test_paypal_error(self):
        try:
            raise PaypalError(id=520003, message='wat?')
        except Exception as error:
            res = self.resource._handle_500(self.request, error)

        data = json.loads(res.content)
        eq_(data['error_code'], '520003')
        eq_(data['error_message'], 'wat?')


class TestBase(test_utils.TestCase):

    def setUp(self):
        self.request = test_utils.RequestFactory().get('/')
        self.resource = Resource()

    @mock.patch('solitude.base._log_cef')
    def test_cef(self, log_cef):
        self.resource.method_check = mock.Mock()
        with self.assertRaises(ImmediateHttpResponse):
            self.resource.dispatch('POST', self.request, api_name='foo',
                                   resource_name='bar')
        args = log_cef.call_args[0]
        eq_(args[0], 'foo:bar')
        kw = log_cef.call_args[1]
        eq_(kw['msg'], 'foo:bar')
        eq_(kw['config']['cef.product'], 'Solitude')

    @mock.patch('solitude.base.log_cef')
    def test_unknowncef(self, log_cef):
        self.resource.method_check = mock.Mock()
        with self.assertRaises(ImmediateHttpResponse):
            self.resource.dispatch('POST', self.request)

        eq_(log_cef.call_args[0][0], 'unknown:unknown')


class TestSerialize(test_utils.TestCase):

    def setUp(self):
        self.serializer = JWTSerializer()
        self.resource = Resource()

    def test_good(self):
        data = jwt.encode({'jwt-encode-key': 'key', 'foo': 'bar'}, 'secret')
        with self.settings(CLIENT_JWT_KEYS={'key': 'secret'}):
            assert self.serializer.deserialize(data, 'application/jwt')

    def test_no_secret(self):
        data = jwt.encode({'jwt-encode-key': 'key', 'foo': 'bar'}, 'secret')
        with self.assertRaises(JWTDecodeError):
            self.serializer.deserialize(data, 'application/jwt')

    def test_no_key(self):
        data = jwt.encode({'foo': 'bar'}, 'secret')
        with self.assertRaises(JWTDecodeError):
            self.serializer.deserialize(data, 'application/jwt')

    def test_wrong_encoding(self):
        data = jwt.encode({'foo': 'bar'}, 'secret')
        with self.assertRaises(simplejson.decoder.JSONDecodeError):
            self.serializer.deserialize(data, 'application/json')

    def test_jwt_required(self):
        data = json.dumps({'foo': 'bar'})
        with self.settings(REQUIRE_JWT=True):
            with self.assertRaises(JWTDecodeError):
                self.serializer.deserialize(data, 'application/json')


class TestJWT(APITest):
    urls = 'solitude.tests.urls'
    url = '/test/fake/'
    service_url = '/test/fake-service/'

    def test_just_json(self):
        res = self.client.post(self.url, json.dumps({'foo': 'bar'}))
        eq_(res.status_code, 201, res.content)

    def test_requires_jwt(self):
        with self.settings(REQUIRE_JWT=True):
            res = self.client.post(self.url, json.dumps({'foo': 'bar'}))
            eq_(res.status_code, 401, res.status_code)

    def test_bogus_jwt(self):
        with self.settings(REQUIRE_JWT=True,
                           CLIENT_JWT_KEYS={'f': 'b'}):
            res = self.client.post(self.url, data='1.2',
                                   content_type='application/jwt')
            eq_(res.status_code, 401, res.status_code)

    def test_some_jwt(self):
        with self.settings(REQUIRE_JWT=True,
                           CLIENT_JWT_KEYS={'f': 'b'}):
            enc = jwt.encode({'jwt-encode-key': 'f', 'name': 'x'}, 'b')
            res = self.client.post(self.url, data=enc,
                                   content_type='application/jwt')
            eq_(res.status_code, 201, res.status_code)

    def test_service(self):
        with self.settings(REQUIRE_JWT=True):
            res = self.client.post(self.service_url,
                                   json.dumps({'foo': 'bar'}))
            eq_(res.status_code, 201, res.status_code)

    @mock.patch('solitude.base._log_cef')
    def test_logged_cef(self, log_cef):
        with self.settings(REQUIRE_JWT=True):
            res = self.client.post(self.url, json.dumps({'foo': 'bar'}))
            eq_(res.status_code, 401, res.status_code)
        args = log_cef.call_args[0]
        eq_(args[0], 'JWT is required')
        eq_(args[1], 1)
