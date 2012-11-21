import json

from django.conf import settings
from django.core.urlresolvers import reverse

import mock
from nose.tools import eq_
import requests
import test_utils

from lib.bango.constants import HEADERS_SERVICE_GET
from lib.bango.errors import BangoError

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
class TestBango(test_utils.TestCase):

    def setUp(self):
        self.url = reverse('bango.proxy')

    def test_not_present(self):
        with self.assertRaises(KeyError):
            self.client.post(self.url)

    def test_good(self):
        res = self.client.post(self.url,
                               json.dumps({'adminEmailAddress': 'bar'}),
                               **{'content_type': 'application/json',
                                  HEADERS_SERVICE_GET: 'create-package'})
        eq_(json.loads(res.content)['adminPersonId'], 2)
