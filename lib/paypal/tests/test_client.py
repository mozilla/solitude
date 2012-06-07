from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings

import test_utils
import mock
from nose.tools import eq_

from ..client import Client
from ..errors import PaypalError

good_token = {'token': 'foo', 'secret': 'bar'}


class BaseCase(test_utils.TestCase):

    def setUp(self):
        self.paypal = Client()


class TestClient(BaseCase):

    def test_nvp(self):
        eq_(self.paypal.nvp({'foo': 'bar'}), 'foo=bar')
        eq_(self.paypal.nvp({'foo': 'ba r'}), 'foo=ba%20r')
        eq_(self.paypal.nvp({'foo': 'bar', 'bar': 'foo'}),
                                  'bar=foo&foo=bar')
        eq_(self.paypal.nvp({'foo': ['bar', 'baa']}),
                                  'foo(0)=bar&foo(1)=baa')

    def test_whitelist(self):
        assert self.paypal.whitelist(['http://foo.bar.com'],
                                     whitelist=('http://foo',))
        assert self.paypal.whitelist(['http://foo.ba'],
                                     whitelist=('http://foo', 'http://bar'))
        with self.assertRaises(ValueError):
            self.paypal.whitelist(['http://foo.com'], whitelist=())

    def test_split(self):
        res = self.paypal.receivers('a@a.com', Decimal('1.99'), '123',
                                    chains=((30, 'us@moz.com'),))
        eq_(res['receiverList.receiver(1).amount'], '0.60')
        eq_(res['receiverList.receiver(1).email'], 'us@moz.com')
        eq_(res['receiverList.receiver(0).amount'], '1.99')
        eq_(res['receiverList.receiver(0).email'], 'a@a.com')

    def test_multiple_split(self):
        res = self.paypal.receivers('a@a.com', Decimal('1.99'), '123',
                                    chains=((30, 'us@moz.com'),
                                            (10, 'me@moz.com')))
        eq_(res['receiverList.receiver(2).amount'], '0.20')
        eq_(res['receiverList.receiver(1).amount'], '0.60')
        eq_(res['receiverList.receiver(0).amount'], '1.99')

    def test_no_split(self):
        res = self.paypal.receivers('a@a.com', Decimal('1.99'), '123',
                                    chains=())
        eq_(res['receiverList.receiver(0).amount'], '1.99')

#    @mock.patch('paypal._call')
#    def test_dict_no_split(self, _call):
#        data = self.data.copy()
#        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
#        self.paypal.get_paykey(data)
#        eq_(_call.call_args[0][1]['receiverList.receiver(0).amount'], '10')
#
#    @mock.patch('paypal._call')
#    def test_dict_split(self, _call):
#        data = self.data.copy()
#        data['chains'] = ((13.4, 'us@moz.com'),)
#        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
#        paypal.get_paykey(data)
#        eq_(_call.call_args[0][1]['receiverList.receiver(0).amount'], '10')
#        eq_(_call.call_args[0][1]['receiverList.receiver(1).amount'], '1.34')

    def test_primary_fees(self):
        res = self.paypal.receivers('a@a.com', Decimal('1.99'), '123',
                                    chains=())
        assert 'feesPayer' not in res

    def test_split_fees(self):
        res = self.paypal.receivers('a@a.com', Decimal('1.99'), '123',
                                    chains=((30, 'us@moz.com'),))
        eq_(res['feesPayer'], 'SECONDARYONLY')


@mock.patch.object(Client, '_call')
class TestRefundPermissions(BaseCase):

    def test_get_permissions_url(self, _call):
        _call.return_value = {'token': 'foo'}
        assert 'foo' in self.paypal.get_permission_url('', [])

    def test_get_permissions_url_error(self, _call):
        _call.side_effect = PaypalError
        with self.assertRaises(PaypalError):
            self.paypal.get_permission_url('', [])

    def test_get_permissions_url_scope(self, _call):
        _call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        self.paypal.get_permission_url('', ['REFUND', 'FOO'])
        eq_(_call.call_args[0][1]['scope'], ['REFUND', 'FOO'])

    def test_check_permission_fail(self, _call):
        _call.return_value = {'scope(0)': 'HAM_SANDWICH'}
        assert not self.paypal.check_permission(good_token, ['REFUND'])

    def test_check_permission(self, _call):
        _call.return_value = {'scope(0)': 'REFUND'}
        eq_(self.paypal.check_permission(good_token, ['REFUND']), True)

    def test_check_permission_error(self, _call):
        _call.side_effect = PaypalError
        with self.assertRaises(PaypalError):
            self.paypal.check_permission(good_token, ['REFUND'])

    def test_get_permissions_token(self, _call):
        _call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        eq_(self.paypal.get_permission_token('foo', ''), good_token)

    def test_get_permissions_subset(self, _call):
        _call.return_value = {'scope(0)': 'REFUND', 'scope(1)': 'HAM'}
        eq_(self.paypal.check_permission(good_token, ['REFUND', 'HAM']), True)
        eq_(self.paypal.check_permission(good_token, ['REFUND', 'JAM']), False)
        eq_(self.paypal.check_permission(good_token, ['REFUND']), True)

good_preapproval_string = {
    'responseEnvelope.build': '2279004',
    'responseEnvelope.ack': 'Success',
    'responseEnvelope.timestamp': '2011-12-13T16:11:34.567-08:00',
    'responseEnvelope.correlationId': '56aaa9b53b12f',
    'preapprovalKey': 'PA-2L635945UC9045439'
}


@mock.patch.object(Client, '_call')
class TestPreApproval(BaseCase):

    def get_data(self):
        return [datetime.today(), datetime.today() + timedelta(days=365),
                'http://foo/return', 'http://foo/cancel']

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
    def test_preapproval_works(self, _call):
        _call.return_value = good_preapproval_string
        eq_(self.paypal.get_preapproval_key(*self.get_data()),
            {'key': 'PA-2L635945UC9045439'})

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
    def test_preapproval_amount(self, _call):
        _call.return_value = good_preapproval_string
        data = self.get_data()
        self.paypal.get_preapproval_key(*data)
        eq_(_call.call_args[0][1]['maxTotalAmountOfAllPayments'], '2000')

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
    def test_preapproval_limits(self, _call):
        _call.return_value = good_preapproval_string
        data = self.get_data()
        self.paypal.get_preapproval_key(*data)
        eq_(_call.call_args[0][1]['paymentPeriod'], 'DAILY')
        eq_(_call.call_args[0][1]['maxAmountPerPayment'], 15)
        eq_(_call.call_args[0][1]['maxNumberOfPaymentsPerPeriod'], 15)

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://bar'))
    def test_naughty(self, _call):
        with self.assertRaises(ValueError):
            data = self.get_data()
            self.paypal.get_preapproval_key(*data)
