import json

from django.core.cache import cache

from mock import patch
from nose.tools import eq_

from solitude.base import APITest


class TestStatus(APITest):

    def setUp(self):
        self.api_name = 'services'
        self.list_url = self.get_list_url('status')

    def test_working_status(self):
        res = self.client.get(self.list_url)
        eq_(res.status_code, 200)

    @patch.object(cache, 'get', lambda x: None)
    def test_failure_status(self):
        res = self.client.get(self.list_url)
        eq_(res.status_code, 500)
        data = json.loads(res.content)
        eq_(data['error_message'], '<Status: database: True, cache: False>')


class TestError(APITest):

    def setUp(self):
        self.api_name = 'services'
        self.list_url = self.get_list_url('error')

    def test_throws_error(self):
        res = self.client.get(self.list_url)
        eq_(res.status_code, 500)
        data = json.loads(res.content)
        eq_(data['error_message'], 'This is a test.')
