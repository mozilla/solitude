import json

from django.conf import settings
from django.core.cache import cache

from mock import patch
from nose.tools import eq_

from solitude.base import APITest
from lib.services.resources import StatusObject


@patch.object(settings, 'DEBUG', False)
class TestStatus(APITest):

    def setUp(self):
        self.api_name = 'services'
        self.list_url = self.get_list_url('status')

    def failed(self, res, on):
        eq_(res.status_code, 500)
        data = json.loads(res.content)
        assert '%s: False' % on in data['error_message'], data

    @patch.object(cache, 'get', lambda x: None)
    def test_failure_status(self):
        res = self.client.get(self.list_url)
        self.failed(res, 'cache')

    # Note that Django will use the values in the settings, altering
    # CACHES right now will still work if your settings allow it. Urk.
    @patch.object(StatusObject, 'test_cache')
    @patch.object(StatusObject, 'test_db')
    def test_proxy(self, test_db, test_cache):
        with self.settings(SOLITUDE_PROXY=True,
                           DATABASES={'default': {'ENGINE': ''}},
                           CACHES={}):
            res = self.client.get(self.list_url)
            eq_(res.status_code, 200, res.content)

    @patch.object(StatusObject, 'test_cache')
    @patch.object(StatusObject, 'test_db')
    def test_proxy_db(self, test_db, test_cache):
        with self.settings(SOLITUDE_PROXY=True,
                           DATABASES={'default': {'ENGINE': 'foo'}},
                           CACHES={}):
            self.failed(self.client.get(self.list_url), 'settings')


@patch.object(settings, 'DEBUG', False)
class TestError(APITest):

    def setUp(self):
        self.api_name = 'services'
        self.list_url = self.get_list_url('error')

    def test_throws_error(self):
        res = self.client.get(self.list_url)
        eq_(res.status_code, 500)
        data = json.loads(res.content)
        eq_(data['error_message'], 'This is a test.')


class TestNoop(APITest):

    def test_noop(self):
        self.api_name = 'services'
        eq_(self.client.get(self.get_list_url('request')).status_code, 200)
