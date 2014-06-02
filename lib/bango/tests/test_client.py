# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured

import mock
import test_utils
from nose.tools import eq_, raises

import samples
from ..client import (Client, ClientMock, ClientProxy, dict_to_mock,
                      get_client, get_request, get_wsdl, Proxy,
                      response_to_dict)
from ..constants import OK, ACCESS_DENIED
from ..errors import AuthError, BangoError, ProxyError


class TestClient(test_utils.TestCase):

    def setUp(self):
        self.client = get_client()

    def test_create_package(self):
        res = self.client.CreatePackage(samples.good_address)
        eq_(res.responseCode, OK)
        assert res.packageId > 1

    @mock.patch.object(ClientMock, 'mock_results')
    def test_auth_failure(self, mock_results):
        mock_results.return_value = {'responseCode': ACCESS_DENIED}
        with self.assertRaises(AuthError):
            self.client.CreatePackage(samples.good_address)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_failure(self, mock_results):
        mock_results.return_value = {'responseCode': 'wat'}
        with self.assertRaises(BangoError):
            self.client.CreatePackage(samples.good_address)

    def test_update_support_email(self):
        res = self.client.UpdateSupportEmailAddress(samples.good_email)
        eq_(res.responseCode, OK)

    def test_update_financial_email(self):
        res = self.client.UpdateFinanceEmailAddress(samples.good_email)
        eq_(res.responseCode, OK)

    def test_create_bango_number(self):
        res = self.client.CreateBangoNumber(samples.good_bango_number)
        eq_(res.responseCode, OK)

    def test_make_premium(self):
        res = self.client.MakePremiumPerAccess(samples.good_make_premium)
        eq_(res.responseCode, OK)


class TestRightClient(test_utils.TestCase):

    def test_no_proxy(self):
        with self.settings(BANGO_PROXY=None, SOLITUDE_PROXY=False):
            assert isinstance(get_client(), Client)

    def test_using_proxy(self):
        with self.settings(BANGO_MOCK=False, BANGO_PROXY='http://foo.com'):
            assert isinstance(get_client(), ClientProxy)

    def test_am_proxy(self):
        with self.settings(BANGO_PROXY='http://foo.com', SOLITUDE_PROXY=True):
            assert isinstance(get_client(), Client)

    def test_mock(self):
        with self.settings(BANGO_MOCK=True):
            assert isinstance(get_client(), ClientMock)

    @raises(ImproperlyConfigured)
    def test_nope(self):
        with self.settings(BANGO_MOCK=False, BANGO_AUTH={'PASSWORD': ''}):
            get_client()


class TestProxy(test_utils.TestCase):

    def setUp(self):
        self.bango = ClientProxy()
        self.url = 'http://foo.com'

    @mock.patch('lib.bango.client.post')
    def test_call(self, post):
        resp = mock.Mock()
        resp.status_code = 200
        resp.content = samples.premium_response
        post.return_value = resp

        with self.settings(BANGO_PROXY=self.url):
            self.bango.MakePremiumPerAccess(samples.good_make_premium)

        args = post.call_args
        eq_(args[0][0], self.url)
        eq_(args[1]['headers']['x-solitude-service'],
            'https://webservices.test.bango.org/mozillaexporter/service.asmx')

    @mock.patch('lib.bango.client.post')
    def test_failure(self, post):
        resp = mock.Mock()
        resp.status_code = 500
        post.return_value = resp

        with self.settings(BANGO_PROXY=self.url):
            with self.assertRaises(ProxyError):
                self.bango.MakePremiumPerAccess(samples.good_make_premium)

    @mock.patch('lib.bango.client.post')
    def test_ok(self, post):
        resp = mock.Mock()
        resp.status_code = 200
        resp.content = samples.package_response
        post.return_value = resp

        with self.settings(BANGO_PROXY=self.url):
            address = samples.good_address.copy()
            del address['seller']
            res = self.bango.CreatePackage(address)
            eq_(res.packageId, 1)
            assert 'CreatePackageResponse' in str(res)

    def test_headers(self):
        eq_(Proxy().get_headers('http://foo.com', {'SOAPAction': 'foo'}),
            {'x-solitude-soapaction': 'foo',
             'x-solitude-service': 'http://foo.com'})


def test_convert_data():
    data = {'foo': 'bar'}
    eq_(data, response_to_dict(dict_to_mock(data)))


def test_callable():
    data = {'foo': lambda: 'x'}
    assert callable(dict_to_mock(data).foo)
    assert not callable(dict_to_mock(data, callables=True).foo)


class TestRequest(test_utils.TestCase):

    def test_mapping(self):
        eq_(get_request('foo'), 'fooRequest')
        eq_(get_request('CreateBillingConfiguration'),
            'CreateBillingConfigurationRequest')
        with self.settings(BANGO_BILLING_CONFIG_V2=True):
            eq_(get_request('CreateBillingConfiguration'),
                'InnerCreateBillingConfigurationRequest')

    def test_file(self):
        assert get_wsdl('billing').endswith('billing_configuration.wsdl')
        with self.settings(BANGO_BILLING_CONFIG_V2=True):
            assert (get_wsdl('billing')
                    .endswith('billing_configuration_v2_0.wsdl'))
