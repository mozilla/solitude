import json

from mock import patch
from nose.tools import eq_

from lib.sellers.models import Seller, SellerPaypal
from solitude.base import APITest


@patch('lib.paypal.resources.pay.Client.get_permission_url')
class TestGetPermissionURL(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.list_url = self.get_list_url('permission-url')

    def get_data(self):
        return {'url': 'http://foo.com/callback.url',
                'scope': ['REFUND', 'ACCESS_BASIC_PERSONAL_DATA']}

    def test_permission(self, key):
        url = 'http://some.paypal.url'
        key.return_value = {'token': url}
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201)
        content = json.loads(res.content)
        eq_(content['token'], 'http://some.paypal.url')

    def test_not_permission(self, key):
        data = self.get_data()
        data['scope'] = 'FAKE'
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)


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
        self.uuid = 'sample:uuid'
        self.seller = Seller.objects.create(uuid=self.uuid)
        self.seller_paypal = SellerPaypal.objects.create(seller=self.seller)
        self.list_url = self.get_list_url('permission-token')

    def get_data(self):
        return {'token': 'foo', 'code': 'bar', 'seller': 'sample:uuid'}

    def test_check_no_seller(self, key):
        data = self.get_data()
        del data['seller']
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)

    def test_check_permission(self, key):
        key.return_value = {'token': 'token', 'secret': 'secret'}
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201, res.content)
        content = json.loads(res.content)
        eq_(content['token'], True)
        eq_(content['secret'], True)

        paypal = SellerPaypal.objects.get(pk=self.seller_paypal.pk)
        eq_(paypal.token, 'token')
        eq_(paypal.secret, 'secret')
