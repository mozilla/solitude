import json

from mock import patch
from nose.tools import eq_

from lib.sellers.models import Seller, SellerPaypal
from solitude.base import APITest


@patch('lib.paypal.resources.pay.Client.get_pay_key')
class TestPreapprovalPaypal(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.list_url = self.get_list_url('pay')
        self.seller = Seller.objects.create(uuid=self.uuid)
        SellerPaypal.objects.create(seller=self.seller,
                                    paypal_id='foo@bar.com')
        self.return_value = {'pay_key': 'foo', 'status': 'CREATED'}

    def get_data(self):
        return {'amount': '5',
                'currency': 'USD',
                'return_url': 'http://foo.com/return.url',
                'ipn_url': 'http://foo.com/return.url',
                'cancel_url': 'http://foo.com/cancel.url',
                'seller': self.uuid}

    def test_post(self, key):
        key.return_value = self.return_value
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201)
        content = json.loads(res.content)
        eq_(content['pay_key'], 'foo')
        eq_(content['status'], 'CREATED')
