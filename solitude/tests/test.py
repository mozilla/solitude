import json
from hashlib import md5

from django import forms
from django import test

import mock
from nose.tools import eq_, raises
from tastypie.exceptions import ImmediateHttpResponse, InvalidFilterError

from lib.buyers.models import Buyer
from lib.sellers.models import Seller
from lib.sellers.resources import SellerResource
from solitude.base import APITest, Resource, etag_func
from solitude.fields import URLField


class TestError(test.TestCase):

    def setUp(self):
        self.request = test.RequestFactory().get('/')
        self.resource = Resource()

    def test_error(self):
        res = None
        try:
            1 / 0
        except Exception as error:
            res = self.resource._handle_500(self.request, error)

        data = json.loads(res.content)
        eq_(data['error_code'], 'ZeroDivisionError')
        eq_(data['error_message'], 'integer division or modulo by zero')


class TestBase(test.TestCase):

    def setUp(self):
        self.request = test.RequestFactory().get(
            '/',
            CONTENT_TYPE='application/json')
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

    def test_etag_func(self):
        assert etag_func(None, 'foo') is None
        etag_value = 123456789
        data = mock.Mock()
        data.obj.etag = etag_value
        eq_(etag_func(None, data), md5(str(etag_value)).hexdigest())
        data = {}
        data['objects'] = []
        eq_(etag_func(None, data), None)
        data = {}
        data['objects'] = [mock.Mock(etag=etag_value)]
        eq_(etag_func(None, data), md5(str(etag_value)).hexdigest())


class TestHeaders(APITest):
    api_name = 'generic'

    def test_content_headers_list(self):
        Buyer.objects.create(uuid='sample:uuid')
        res = self.client.get(self.get_list_url('buyer'))
        assert 'etag' in res._headers

    def test_content_headers_detail(self):
        buyer = Buyer.objects.create(uuid='sample:uuid')
        res = self.client.get(self.get_detail_url('buyer', buyer))
        assert 'etag' in res._headers
        eq_(md5(str(buyer.etag)).hexdigest(),
            res._headers['etag'][1][1:-1])

    def test_content_headers_etag_get(self):
        buyer = Buyer.objects.create(uuid='sample:uuid')
        etag = md5(str(buyer.etag)).hexdigest()
        res = self.client.get(self.get_list_url('buyer'),
                              HTTP_IF_NONE_MATCH=etag)
        eq_(res.status_code, 304)
        res = self.client.get(self.get_detail_url('buyer', buyer),
                              HTTP_IF_NONE_MATCH=etag)
        eq_(res.status_code, 304)

    def test_content_headers_etag_put(self):
        buyer = Buyer.objects.create(uuid='sample:uuid', pin='1234')
        res = self.client.get(self.get_detail_url('buyer', buyer))
        etag = res._headers['etag'][1][1:-1]
        res = self.client.put(self.get_detail_url('buyer', buyer),
                              data={'uuid': buyer.uuid,
                                    'pin': '5678'},
                              HTTP_IF_MATCH=etag)
        eq_(res.status_code, 202)
        buyer.save()
        res = self.client.put(self.get_detail_url('buyer', buyer),
                              data={'uuid': buyer.uuid,
                                    'pin': '9101'},
                              HTTP_IF_MATCH=etag)
        eq_(res.status_code, 412)
        res = self.client.put(self.get_detail_url('buyer', buyer),
                              data={'uuid': buyer.uuid,
                                    'pin': '9101'})
        eq_(res.status_code, 202)

    def test_content_headers_etag_patch(self):
        buyer = Buyer.objects.create(uuid='sample:uuid', pin='1234')
        res = self.client.get(self.get_detail_url('buyer', buyer))
        etag = res._headers['etag'][1][1:-1]
        res = self.client.patch(self.get_detail_url('buyer', buyer),
                                data={'pin': '5678'},
                                HTTP_IF_MATCH=etag)
        eq_(res.status_code, 202)
        buyer.save()
        res = self.client.patch(self.get_detail_url('buyer', buyer),
                                data={'pin': '9101'},
                                HTTP_IF_MATCH=etag)
        eq_(res.status_code, 412)
        res = self.client.patch(self.get_detail_url('buyer', buyer),
                                data={'pin': '9101'})
        eq_(res.status_code, 202)


class TestURLField(test.TestCase):

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

    def test_kwargs(self):
        obj = Seller.objects.create()
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        self.field.clean('/generic/seller/{0}/'.format(obj.pk))


class TestModel(test.TestCase):

    def test_safer_get_or_create(self):
        data = dict(uuid='some-unique-value')
        a, c = Seller.objects.safer_get_or_create(**data)
        assert c
        b, c = Seller.objects.safer_get_or_create(**data)
        assert not c
        eq_(a, b)
