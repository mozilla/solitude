import json

from mock import patch
from nose.tools import eq_

from solitude.base import APITest


@patch('lib.paypal.resources.pay.Client.get_permission_url')
class TestGetPermissionURL(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.list_url = self.get_list_url('permission-url')

    def get_data(self):
        return {'url': 'http://foo.com/callback.url',
                'scope': 'foo'}

    def test_permission(self, key):
        url = 'http://some.paypal.url'
        key.return_value = {'token': url}
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201)
        content = json.loads(res.content)
        eq_(content['token'], 'http://some.paypal.url')


@patch('lib.paypal.resources.pay.Client.check_permission')
class TestCheckPermission(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.list_url = self.get_list_url('permission-check')

    def get_data(self):
        return {'token': 'foo', 'permissions': 'REFUND'}

    def test_check_permission(self, key):
        key.return_value = {'status': True}
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201, res.content)
        content = json.loads(res.content)
        eq_(content['status'], True)


@patch('lib.paypal.resources.pay.Client.get_permission_token')
class TestGetPermissionToken(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.list_url = self.get_list_url('permission-token')

    def get_data(self):
        return {'token': 'foo', 'code': 'bar'}

    def test_check_permission(self, key):
        key.return_value = {'token': 'token', 'secret': 'secret'}
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201, res.content)
        content = json.loads(res.content)
        eq_(content['token'], 'token')
        eq_(content['secret'], 'secret')
