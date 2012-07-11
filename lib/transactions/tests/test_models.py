from mock import patch
from nose.tools import eq_

from lib.sellers.models import Seller, SellerPaypal
from lib.transactions import constants
from lib.transactions.models import PaypalTransaction
from solitude.base import APITest


class TestTransaction(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.pay_url = self.get_list_url('pay')
        self.check_url = self.get_list_url('pay-check')
        self.seller = Seller.objects.create(uuid=self.uuid)
        SellerPaypal.objects.create(seller=self.seller,
                                    paypal_id='foo@bar.com')

    def get_data(self):
        return {'amount': '5',
                'currency': 'USD',
                'return_url': 'http://foo.com/return.url',
                'ipn_url': 'http://foo.com/ipn.url',
                'cancel_url': 'http://foo.com/cancel.url',
                'memo': 'Some memo',
                'seller': self.uuid}

    @patch('lib.paypal.resources.pay.Client.get_pay_key')
    def test_pay(self, key):
        key.return_value = {'pay_key': 'foo', 'status': 'CREATED',
                            'correlation_id': '123', 'uuid': '456'}
        res = self.client.post(self.pay_url, data=self.get_data())
        eq_(res.status_code, 201)
        qs = PaypalTransaction.objects.all()
        eq_(qs.count(), 1)

        obj = qs[0]
        eq_(obj.amount, 5)
        eq_(obj.correlation_id, '123')
        eq_(obj.uuid, '456')
        eq_(obj.seller, self.seller.paypal)
        eq_(obj.status, constants.STATUS_PENDING)

    @patch('lib.paypal.resources.pay.Client.check_purchase')
    def test_checked(self, check):
        check.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        pp = PaypalTransaction.objects.create(pay_key='foo', amount=5,
                                              seller=self.seller.paypal)
        res = self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(res.status_code, 201)
        eq_(PaypalTransaction.objects.get(pk=pp.pk).status,
            constants.STATUS_CHECKED)

    @patch('lib.paypal.resources.pay.Client.check_purchase')
    def test_complete(self, check):
        check.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        pp = PaypalTransaction.objects.create(pay_key='foo', amount=5,
                                              seller=self.seller.paypal)
        self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(PaypalTransaction.objects.get(pk=pp.pk).status,
            constants.STATUS_CHECKED)

        pp.status = constants.STATUS_COMPLETED
        pp.save()
        self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(PaypalTransaction.objects.get(pk=pp.pk).status,
            constants.STATUS_COMPLETED)

    @patch('lib.paypal.resources.pay.Client.check_purchase')
    def test_complete_not_there(self, check):
        check.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        PaypalTransaction.objects.create(pay_key='bar', amount=5,
                                         seller=self.seller.paypal)
        res = self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(res.status_code, 404)
