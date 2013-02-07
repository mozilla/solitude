import json

from django import forms
from django.conf import settings

import jwt
import mock
from nose.tools import eq_, raises
import simplejson
from tastypie.exceptions import ImmediateHttpResponse, InvalidFilterError
import test_utils

from lib.paypal.errors import PaypalError
from lib.sellers.models import Seller
from lib.sellers.resources import SellerResource
from solitude.base import APITest, JWTDecodeError, JWTSerializer, Resource
from solitude.fields import URLField


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
        eq_(data['error_code'], 'ZeroDivisionError')
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
        self.request = test_utils.RequestFactory().get('/',
            CONTENT_TYPE='application/json')
        self.resource = Resource()
        self.resource._meta.serializer = JWTSerializer()

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

    def test_build_filters_fails(self):
        with self.assertRaises(InvalidFilterError):
            self.resource.build_filters({'foo': 'bar'})

    def test_build_filters_passes(self):
        check = mock.Mock()
        check.return_value = ['foo']
        self.resource.check_filtering = check
        self.resource.fields = ['foo']
        eq_(self.resource.build_filters({'foo': 'bar'}),
            {'foo__exact': 'bar'})

    def test_deserialize(self):
        self.request._body = ''
        eq_(self.resource.deserialize_body(self.request), {})
        self.request._body = json.dumps({'foo': 'bar'})
        eq_(self.resource.deserialize_body(self.request)['foo'], 'bar')


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


@mock.patch.object(settings, 'DEBUG', False)
class TestJWT(APITest):
    urls = 'solitude.tests.urls'
    url = '/test/fake/'

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

    @mock.patch('solitude.base._log_cef')
    def test_logged_cef(self, log_cef):
        with self.settings(REQUIRE_JWT=True):
            res = self.client.post(self.url, json.dumps({'foo': 'bar'}))
            eq_(res.status_code, 401, res.status_code)
        args = log_cef.call_args[0]
        eq_(args[0], 'JWT is required')
        eq_(args[1], 10)


class TestURLField(test_utils.TestCase):

    def test_valid(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_nope(self):
        self.field = URLField(to='lib.sellers.resources.Nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_module(self):
        self.field = URLField(to='lib.nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_more_module(self):
        self.field = URLField(to='nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(forms.ValidationError)
    def test_not_there(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        self.field.clean('/generic/seller/1/')

    @raises(forms.ValidationError)
    def test_not_found(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        self.field.clean('/blarg/blarg/1/')

    def test_empty(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource',
                              required=False)
        eq_(self.field.clean(''), None)


class TestModel(test_utils.TestCase):

    def test_safer_get_or_create(self):
        data = dict(uuid='some-unique-value')
        a, c = Seller.objects.safer_get_or_create(**data)
        assert c
        b, c = Seller.objects.safer_get_or_create(**data)
        assert not c
        eq_(a, b)
