import json

from mock import patch
from nose.tools import eq_

from lib.sellers.models import Seller, SellerPaypal
from lib.transactions.models import PaypalTransaction
from solitude.base import APITest


@patch('lib.paypal.resources.pay.Client.get_pay_key')
class TestPayPaypal(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.list_url = self.get_list_url('pay')
        self.seller = Seller.objects.create(uuid=self.uuid)
        SellerPaypal.objects.create(seller=self.seller,
                                    paypal_id='foo@bar.com')
        self.return_value = {'pay_key': 'foo', 'status': 'CREATED',
                             'correlation_id': '123', 'uuid': '456'}


    def get_data(self):
        return {'amount': '5',
                'currency': 'USD',
                'return_url': 'http://foo.com/return.url',
                'ipn_url': 'http://foo.com/ipn.url',
                'cancel_url': 'http://foo.com/cancel.url',
                'memo': 'Some memo',
                'seller': self.uuid}

    def test_post(self, key):
        key.return_value = self.return_value
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201)
        qs = PaypalTransaction.objects.all()
        eq_(qs.count(), 1)
        obj = qs[0]
        eq_(obj.amount, 5)
        eq_(obj.currency, 'USD')
        eq_(obj.correlation_id, '123')
        eq_(obj.uuid, '456')
        eq_(obj.seller, self.seller.paypal)
