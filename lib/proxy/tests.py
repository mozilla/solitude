import json

from django.conf import settings
from django.core.urlresolvers import reverse

import mock
from nose.tools import eq_
import requests
import test_utils

from lib.bango.constants import HEADERS_SERVICE_GET
from lib.bango.tests import samples

from lib.paypal.constants import HEADERS_URL_GET, HEADERS_TOKEN_GET
from lib.paypal.map import urls


@mock.patch.object(settings, 'SOLITUDE_PROXY', True)
@mock.patch('lib.proxy.views.requests.post')
class TestProxy(test_utils.TestCase):

    def setUp(self):
        self.url = reverse('paypal.proxy')

    def test_proxy(self, post):
        post.return_value.status_code = 200
        post.return_value.text = 'some-text'
        res = self.client.post(self.url, **{HEADERS_URL_GET: 'get-pay-key'})
        eq_(post.call_args[0][0], urls['get-pay-key'])
        eq_(res.status_code, 200)
        eq_(res.content, 'some-text')

    def test_not_present(self, post):
        with self.assertRaises(KeyError):
            self.client.post(self.url)

    def test_proxy_auth(self, post):
        post.return_value.status_code = 200
        self.client.get(self.url, **{HEADERS_URL_GET: 'get-pay-key',
                                     HEADERS_TOKEN_GET: 'token=b&secret=f'})
        assert 'X-PAYPAL-AUTHORIZATION' in post.call_args[1]['headers']

    def test_status_code(self, post):
        post.return_value.status_code = 123
        res = self.client.post(self.url, **{HEADERS_URL_GET: 'get-pay-key'})
        eq_(res.status_code, 123)

    def test_result(self, post):
        post.side_effect = requests.exceptions.ConnectionError
        res = self.client.post(self.url, **{HEADERS_URL_GET: 'get-pay-key'})
        eq_(res.status_code, 500)

    def test_not_enabled(self, post):
        with self.settings(SOLITUDE_PROXY=False):
            eq_(self.client.post(self.url).status_code, 404)


@mock.patch.object(settings, 'SOLITUDE_PROXY', True)
@mock.patch.object(settings, 'BANGO_MOCK', True)
@mock.patch.object(settings, 'BANGO_AUTH', {'USER': 'me', 'PASSWORD': 'shh'})
@mock.patch('lib.proxy.views.requests.post')
class TestBango(test_utils.TestCase):

    def setUp(self):
        self.url = reverse('bango.proxy')

    def test_not_present(self, post):
        with self.assertRaises(KeyError):
            self.client.post(self.url, samples.sample_request,
                             **{'content_type': 'text/xml'})

    def test_good(self, post):
        self.client.post(self.url,
                         samples.sample_request,
                         **{'content_type': 'text/xml',
                            HEADERS_SERVICE_GET: 'http://url.com/b'})
        body = post.call_args[1]['data']
        assert '<ns0:username>me</ns0:username>' in body
        assert '<ns0:password>shh</ns0:password>' in body

    def test_billing(self, post):
        self.client.post(self.url,
                         samples.billing_request,
                         **{'content_type': 'text/xml',
                            HEADERS_SERVICE_GET: 'http://url.com/b'})
        body = post.call_args[1]['data']
        assert '<ns1:username>me</ns1:username>' in body
        assert '<ns1:password>shh</ns1:password>' in body
