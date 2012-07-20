from decimal import Decimal
import json

from django.conf import settings

from mock import Mock, patch
from nose.tools import eq_

from ..check import Check
from ..client import Client
from ..errors import PaypalError

from lib.sellers.models import Seller, SellerPaypal
from solitude.base import APITest

import test_utils


class TestCheck(test_utils.TestCase):

    def setUp(self):
        self.paypal_id = 'foo@bar.com'
        self.paypal_permissions_token = 'foo'
        self.prices = [('USD', Decimal('1.00'))]
        self.multiple_prices = self.prices + [('EUR', Decimal('0.5'))]
        self.check = Check(self.paypal_id, self.paypal_permissions_token,
                           self.prices)

    def test_passed(self):
        self.check.pass_('id')
        assert self.check.passed, self.check.state

    def test_fail(self):
        self.check.failure('id', 'Something')
        assert not self.check.passed, self.check.state

    def test_id_none(self):
        self.check.paypal_id = None
        self.check.check_id()
        assert not self.check.passed, self.check.state

    @patch.object(Client, 'check_permission')
    def test_refund(self, check_permission):
        check_permission.return_value = {'status': True}
        self.check.check_refund()
        assert self.check.passed, self.check.state

    @patch.object(Client, 'check_permission')
    def test_refund_error(self, check_permission):
        check_permission.side_effect = PaypalError
        self.check.check_refund()
        assert not self.check.passed, self.check.state

    @patch.object(Client, 'get_verified')
    def test_check_id(self, get_verified):
        get_verified.return_value = {'type': u'PERSONAL'}
        self.check.check_id()
        assert not self.check.passed, self.check.state

    @patch.object(Client, 'get_verified')
    def test_check_id_business(self, get_verified):
        get_verified.return_value = {'type': u'BUSINESS'}
        self.check.check_id()
        assert self.check.passed, self.check.state

    @patch.object(Client, 'get_verified')
    def test_check_id_premier(self, get_verified):
        get_verified.return_value = {'type': u'PREMIER'}
        self.check.check_id()
        assert self.check.passed, self.check.state

    @patch.object(Client, 'get_verified')
    def test_check_id_nope(self, get_verified):
        get_verified.side_effect = PaypalError
        self.check.check_id()
        assert not self.check.passed, self.check.state

    @patch.object(Client, 'get_pay_key')
    def test_currency(self, get_pay_key):
        self.check.prices = self.multiple_prices
        self.check.check_currencies()
        eq_(get_pay_key.call_args_list[0][1]['currency'], 'USD')
        eq_(get_pay_key.call_args_list[1][1]['currency'], 'EUR')
        assert self.check.passed, self.check.state

    @patch.object(Client, 'get_pay_key')
    def test_currency_fails(self, get_pay_key):
        get_pay_key.side_effect = PaypalError()
        self.check.check_currencies()
        assert not self.check.passed, self.check.state
        eq_(self.check.errors,
            ['Failed to make a test transaction in USD.'])

    @patch.object(settings, 'PAYPAL_URL_WHITELIST', ())
    @patch.object(Client, 'get_pay_key')
    def test_whitelist_fails(self, get_pay_key):
        with self.assertRaises(IndexError):
            self.check.check_currencies()

    def test_no_currency(self):
        self.check.prices = None
        self.check.check_currencies()
        assert not self.check.passed, self.check.state
        eq_(self.check.errors,
            ['No prices specified.'])


@patch('lib.paypal.resources.check.Check')
class TestAccountCheck(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uid = 'sample:uid'
        self.list_url = self.get_list_url('account-check')
        self.seller = Seller.objects.create(uuid=self.uid)
        self.paypal = SellerPaypal.objects.create(seller=self.seller,
                                                  token='f', paypal_id='b')
        self.mock = Mock()

    def test_check(self, check):
        self.mock.passed = True
        check.return_value = self.mock
        res = self.client.post(self.list_url, data={'seller': self.uid})
        eq_(res.status_code, 201)
        eq_(json.loads(res.content)['passed'], True)
