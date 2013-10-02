from decimal import Decimal
import json
import urllib

from mock import Mock, patch
from nose.tools import eq_

import test_utils

from lib.paypal import constants
from lib.paypal.ipn import IPN
from lib.paypal.tests import samples
from lib.sellers.models import Seller, SellerPaypal
from lib.sellers.tests.utils import make_seller_paypal
from lib.transactions import constants as transaction_constants
from lib.transactions.models import Transaction
from solitude.base import APITest


@patch('lib.paypal.client.requests.post')
class TestValid(test_utils.TestCase):

    def test_empty(self, post):
        eq_(IPN('').is_valid(), False)

    def test_not_completed(self, post):
        eq_(IPN('status=something').is_valid(), False)

    def test_not_valid(self, post):
        post.return_value.text = 'NOPE'
        post.return_value.status_code = 200
        eq_(IPN('status=completed').is_valid(), False)

    def test_good(self, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        eq_(IPN('status=completed').is_valid(), True)

    def test_calls(self, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        eq_(IPN('status=completed').is_valid(), True)


class TestParse(test_utils.TestCase):

    def create(self, data):
        ipn = IPN(data)
        mock = Mock()
        mock.return_value = True
        ipn.is_valid = mock
        return ipn

    def test_parse(self):
        ipn = self.create('status=foo')
        eq_(ipn.parse(), ({'status': 'foo'}, {}))

    def test_number(self):
        ipn = self.create(urllib.urlencode({'transaction[0].amount':
                                            'USD 1.00'}))
        eq_(ipn.parse(), ({}, {'0': {'amount': {'currency': 'USD',
                                                'amount': Decimal('1.00')}}}))

    def test_sample_refund(self):
        ipn = self.create(urllib.urlencode(samples.sample_refund))
        trans, item = ipn.parse()
        eq_(trans['status'], 'COMPLETED')
        eq_(item['0']['status'], 'Refunded')
        eq_(item['0']['amount'],
            {'currency': 'USD', 'amount': Decimal('1.00')})

    def test_chained_refund(self):
        ipn = self.create(urllib.urlencode(samples.sample_chained_refund))
        trans, res = ipn.parse()
        eq_(trans['status'], 'COMPLETED')
        eq_(res['0']['status'], 'Refunded')
        eq_(res['0']['is_primary_receiver'], 'true')
        eq_(res['0']['amount'],
            {'currency': 'USD', 'amount': Decimal('0.99')})
        eq_(res['1']['is_primary_receiver'], 'false')
        eq_(res['1']['amount'],
            {'currency': 'USD', 'amount': Decimal('0.30')})


@patch('lib.paypal.client.requests.post')
class TestProcess(test_utils.TestCase):

    def test_invalid(self, post):
        ipn = IPN('')
        ipn.process()
        eq_(ipn.status, constants.IPN_STATUS_IGNORED)

    def test_still_ignored(self, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        ipn = IPN(urllib.urlencode(samples.sample_refund))
        ipn.process()
        eq_(ipn.status, constants.IPN_STATUS_IGNORED)

    @patch('lib.paypal.ipn.utils.completed')
    def test_purchase(self, completed, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        completed.return_value = True
        ipn = IPN(urllib.urlencode(samples.sample_purchase))
        ipn.process()
        eq_(ipn.status, constants.IPN_STATUS_OK)

    @patch('lib.paypal.ipn.utils.completed')
    def test_purchase_not(self, completed, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        completed.return_value = False
        ipn = IPN(urllib.urlencode(samples.sample_purchase))
        ipn.process()
        eq_(ipn.status, constants.IPN_STATUS_IGNORED)

    @patch('lib.paypal.ipn.utils.refunded')
    def test_refund(self, refunded, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        refunded.return_value = True
        ipn = IPN(urllib.urlencode(samples.sample_refund))
        ipn.process()
        eq_(ipn.status, constants.IPN_STATUS_OK)

    @patch('lib.paypal.ipn.utils.reversal')
    def test_reversal(self, reversal, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        reversal.return_value = True
        ipn = IPN(urllib.urlencode(samples.sample_reversal))
        ipn.process()
        eq_(ipn.status, constants.IPN_STATUS_OK)

    @patch('lib.paypal.ipn.utils.refunded')
    def test_chained_refund(self, refunded, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        refunded.return_value = True
        ipn = IPN(urllib.urlencode(samples.sample_chained_refund))
        ipn.process()
        eq_(refunded.call_count, 1)
        eq_(ipn.status, constants.IPN_STATUS_OK)


@patch('lib.paypal.client.requests.post')
class TestIPNResource(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.list_url = self.get_list_url('ipn')
        self.seller, self.paypal, self.product = make_seller_paypal(self.uuid)
        self.transaction = Transaction.objects.create(uuid='5678',
            provider=transaction_constants.PROVIDER_PAYPAL,
            seller_product=self.product, amount='10', uid_support='123')

    def test_nope(self, post):
        res = self.client.post(self.list_url, data={})
        eq_(res.status_code, 400, res.content)

    def test_something(self, post):
        res = self.client.post(self.list_url, data={'data': 'foo'})
        eq_(res.status_code, 201)
        eq_(json.loads(res.content)['status'], 'IGNORED')

    def test_purchase(self, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        res = self.client.post(self.list_url, data={'data':
                urllib.urlencode(samples.sample_purchase)})
        eq_(res.status_code, 201)
        data = json.loads(res.content)
        eq_(data['status'], 'OK')
        eq_(data['action'], 'PAYMENT')
        eq_(data['uuid'], '5678')
        eq_(data['amount'], {'currency': 'USD', 'amount': '0.01'})

    def test_refund(self, post):
        post.return_value.text = 'VERIFIED'
        post.return_value.status_code = 200
        self.transaction.status = transaction_constants.STATUS_COMPLETED
        self.transaction.save()
        res = self.client.post(self.list_url, data={'data':
                urllib.urlencode(samples.sample_refund)})
        eq_(res.status_code, 201)
        data = json.loads(res.content)
        eq_(data['status'], 'OK')
        eq_(data['action'], 'REFUND')
        eq_(data['uuid'], '5678')
        eq_(data['amount'], {'currency': 'USD', 'amount': '1.00'})
