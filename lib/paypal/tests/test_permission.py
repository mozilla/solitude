import json

from mock import patch
from nose.tools import eq_

from lib.buyers.models import Buyer, BuyerPaypal
from lib.sellers.models import Seller, SellerPaypal
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
