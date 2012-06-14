import json

from mock import patch
from nose.tools import eq_

from solitude.base import APITest


@patch('lib.paypal.resources.pay.Client.get_personal_basic')
class TestGetBasic(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.list_url = self.get_list_url('personal-basic')

    def test_permission(self, key):
        key.return_value = {'first_name': '..'}
        res = self.client.post(self.list_url, data={'token': 'foo'})
        eq_(res.status_code, 201)
        content = json.loads(res.content)
        eq_(content['first_name'], '..')


@patch('lib.paypal.resources.pay.Client.get_personal_advanced')
class TestGetAdvanced(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.list_url = self.get_list_url('personal-advanced')

    def test_permission(self, key):
        key.return_value = {'phone': '..'}
        res = self.client.post(self.list_url, data={'token': 'foo'})
        eq_(res.status_code, 201)
        content = json.loads(res.content)
        eq_(content['phone'], '..')
