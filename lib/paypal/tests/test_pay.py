import json

from mock import patch
from nose.tools import eq_

from lib.buyers.models import Buyer, BuyerPaypal
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
        content = json.loads(res.content)
        eq_(content['pay_key'], 'foo')
        eq_(content['status'], 'CREATED')

    def test_post_missing(self, key):
        data = self.get_data()
        del data['amount']
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'amount'),
            [u'This field is required.'])

    def create_buyer(self):
        buyer = Buyer.objects.create(uuid=self.uuid)
        BuyerPaypal.objects.create(buyer=buyer, key='foo')
        return buyer

    def test_post_preapproval(self, key):
        key.return_value = {'pay_key': 'foo', 'status': 'COMPLETED',
                            'correlation_id': '123', 'uuid': '456'}
        self.create_buyer()
        data = self.get_data()
        data['buyer'] = self.uuid
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 201, res.content)
        eq_(key.call_args[1]['preapproval'], 'foo')

    def test_buyer_but_not_present(self, key):
        key.return_value = {'pay_key': 'foo', 'status': 'COMPLETED',
                            'correlation_id': '123', 'uuid': '456'}
        data = self.get_data()
        data['buyer'] = self.uuid
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 201, res.content)
        # Why does the form return '' and not None.
        eq_(key.call_args[1]['preapproval'], '')


class KeyTest(object):

    def setUp(self):
        self.api_name = 'paypal'
        seller = Seller.objects.create()
        seller_paypal = SellerPaypal.objects.create(seller=seller)
        PaypalTransaction.objects.create(uuid='xyz', pay_key='foo',
                                         seller=seller_paypal, amount=5)

    def test_check_uuid_404(self, key):
        res = self.client.post(self.list_url, data={'uuid': 'xyza'})
        eq_(res.status_code, 404)

    def test_check_neither(self, key):
        res = self.client.post(self.list_url, data={})
        eq_(res.status_code, 400)

    def test_check_both(self, key):
        res = self.client.post(self.list_url, data={'uuid': 'something',
                                                    'pay_key': 'else'})
        eq_(res.status_code, 400)


@patch('lib.paypal.resources.pay.Client.check_purchase')
class TestPurchasePaypal(KeyTest, APITest):

    def setUp(self):
        KeyTest.setUp(self)
        APITest.setUp(self)
        self.list_url = self.get_list_url('pay-check')

    def test_check(self, key):
        key.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        res = self.client.post(self.list_url, data={'pay_key': 'foo'})
        eq_(res.status_code, 201, res.content)
        eq_(json.loads(res.content)['status'], 'COMPLETED')

    def test_check_uuid(self, key):
        key.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        res = self.client.post(self.list_url, data={'uuid': 'xyz'})
        eq_(res.status_code, 201, res.content)
        eq_(json.loads(res.content)['status'], 'COMPLETED')


@patch('lib.paypal.resources.pay.Client.get_refund')
class TestRefundPaypal(KeyTest, APITest):

    def setUp(self):
        KeyTest.setUp(self)
        APITest.setUp(self)
        self.list_url = self.get_list_url('refund')

    def test_refund(self, key):
        key.return_value = {'response': [{'refundFeeAmount': 1}]}
        res = self.client.post(self.list_url, data={'pay_key': 'foo'})
        eq_(res.status_code, 201, res.content)
        eq_(json.loads(res.content)['response'][0]['refundFeeAmount'], 1)

    def test_uuid(self, key):
        key.return_value = {'response': [{'refundFeeAmount': 1}]}
        res = self.client.post(self.list_url, data={'uuid': 'xyz'})
        eq_(res.status_code, 201, res.content)
        eq_(json.loads(res.content)['response'][0]['refundFeeAmount'], 1)
