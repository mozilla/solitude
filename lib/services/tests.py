import json

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_


from solitude.base import APITest
from lib.services.resources import TestError


@patch.object(settings, 'DEBUG', False)
class TestStatus(APITest):

    def setUp(self):
        self.list_url = reverse('services.status')

    def failed(self, res, on):
        eq_(res.status_code, 500)
        data = json.loads(res.content)
        assert False in data.values()

    @patch.object(cache, 'get', lambda x: None)
    def test_failure_status(self):
        res = self.client.get(self.list_url)
        self.failed(res, 'cache')

    # Note that Django will use the values in the settings, altering
    # CACHES right now will still work if your settings allow it. Urk.
    @patch('requests.get')
    @patch('lib.services.resources.StatusObject.test_cache')
    @patch('lib.services.resources.StatusObject.test_db')
    def test_proxy(self, test_db, test_cache, requests):
        test_db.return_value = False
        with self.settings(SOLITUDE_PROXY=True,
                           DATABASES={'default': {'ENGINE': ''}},
                           CACHES={}):
            res = self.client.get(self.list_url)
            eq_(res.status_code, 200, res.content)

    @patch('requests.get')
    @patch('lib.services.resources.StatusObject.test_cache')
    @patch('lib.services.resources.StatusObject.test_db')
    def test_proxy_db(self, test_db, test_cache, requests):
        test_db.return_value = False
        test_cache.return_value = False
        with self.settings(SOLITUDE_PROXY=True,
                           DATABASES={'default': {'ENGINE': 'foo'}},
                           CACHES={}):
            self.failed(self.client.get(self.list_url), 'settings')


class TestErrors(APITest):

    def test_throws_error(self):
        with self.assertRaises(TestError):
            self.client.get(reverse('services.error'))


class TestNoop(APITest):

    def test_noop(self):
        eq_(self.client.get(reverse('services.request')).status_code, 200)
