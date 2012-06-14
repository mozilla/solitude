# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings

import test_utils
import mock
from nose.tools import eq_

from ..client import Client
from ..errors import AuthError, PaypalDataError, PaypalError

good_token = {'token': 'foo', 'secret': 'bar'}


class BaseCase(test_utils.TestCase):

    def setUp(self):
        self.paypal = Client()


@mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
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
            self.paypal.whitelist(['http://foo.com'], whitelist=('http://bar'))

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

    def test_string(self):
        with self.assertRaises(PaypalDataError):
            self.paypal.receivers('a@a.com', 'xyz', '123')

    def test_primary_fees(self):
        res = self.paypal.receivers('a@a.com', Decimal('1.99'), '123',
                                    chains=())
        assert 'feesPayer' not in res

    def test_split_fees(self):
        res = self.paypal.receivers('a@a.com', Decimal('1.99'), '123',
                                    chains=((30, 'us@moz.com'),))
        eq_(res['feesPayer'], 'SECONDARYONLY')

    def test_parse_refund(self):
        res = self.paypal.parse_refund({
            'refundInfoList.refundInfo(1).refundFeeAmount': ['0.02'],
            'refundInfoList.refundInfo(0).refundFeeAmount': ['1.03'],
            'refundInfoList.refundInfo(0).receiver.email': ['bob@example.com'],
            'refundInfoList.refundInfo(1).receiver.amount': ['1.23']})
        eq_(res[0]['refundFeeAmount'], ['1.03'])
        eq_(res[1]['refundFeeAmount'], ['0.02'])
        eq_(res[1]['receiver.amount'], ['1.23'])


@mock.patch.object(Client, '_call')
@mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
class TestRefundPermissions(BaseCase):

    args = ['http://foo.com', 'foo']

    def test_get_permissions_url(self, _call):
        _call.return_value = {'token': 'foo'}
        assert 'foo' in self.paypal.get_permission_url(*self.args)['token']

    def test_get_permissions_url_error(self, _call):
        with self.assertRaises(ValueError):
            self.paypal.get_permission_url('', [])

    def test_get_permissions_url_scope(self, _call):
        _call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        self.paypal.get_permission_url(self.args[0], ['REFUND', 'FOO'])
        eq_(_call.call_args[0][1]['scope'], ['REFUND', 'FOO'])

    def test_check_permission_fail(self, _call):
        _call.return_value = {'scope(0)': 'HAM_SANDWICH'}
        eq_(self.paypal.check_permission(good_token, ['REFUND']),
            {'status': False})

    def test_check_permission(self, _call):
        _call.return_value = {'scope(0)': 'REFUND'}
        eq_(self.paypal.check_permission(good_token, ['REFUND']),
            {'status': True})

    def test_check_permission_error(self, _call):
        _call.side_effect = PaypalError
        with self.assertRaises(PaypalError):
            self.paypal.check_permission(good_token, ['REFUND'])

    def test_get_permissions_token(self, _call):
        _call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        eq_(self.paypal.get_permission_token('foo', ''), good_token)

    def test_get_permissions_subset(self, _call):
        _call.return_value = {'scope(0)': 'REFUND', 'scope(1)': 'HAM'}
        eq_(self.paypal.check_permission(good_token, ['REFUND', 'HAM']),
            {'status': True})
        eq_(self.paypal.check_permission(good_token, ['REFUND', 'JAM']),
            {'status': False})
        eq_(self.paypal.check_permission(good_token, ['REFUND']),
            {'status': True})

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

good_response = ('responseEnvelope.timestamp='
            '2011-01-28T06%3A16%3A33.259-08%3A00&responseEnvelope.ack=Success'
            '&responseEnvelope.correlationId=7377e6ae1263c'
            '&responseEnvelope.build=1655692'
            '&payKey=AP-9GD76073HJ780401K&paymentExecStatus=CREATED')

auth_error = ('error(0).errorId=520003'
            '&error(0).message=Authentication+failed.+API+'
            'credentials+are+incorrect.')


@mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
class TestPayKey(BaseCase):

    def setUp(self):
        super(TestPayKey, self).setUp()
        self.data = ['someone@somewhere.com', 10, 'http://foo/i',
                     'http://foo/c', 'http://foo/r']

    @mock.patch.object(Client, '_call')
    def test_dict_no_split(self, _call):
        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
        self.paypal.get_pay_key(*self.data)
        eq_(_call.call_args[0][1]['receiverList.receiver(0).amount'], '10')

    @mock.patch.object(Client, '_call')
    @mock.patch.object(settings, 'PAYPAL_CHAINS', ((13.4, 'us@moz.com'),))
    def test_dict_split(self, _call):
        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
        self.paypal.get_pay_key(*self.data)
        eq_(_call.call_args[0][1]['receiverList.receiver(0).amount'], '10')
        eq_(_call.call_args[0][1]['receiverList.receiver(1).amount'], '1.34')

    @mock.patch('requests.post')
    def test_get_key(self, post):
        post.return_value.text = good_response
        eq_(self.paypal.get_pay_key(*self.data),
            {'pay_key': 'AP-9GD76073HJ780401K', 'status': 'CREATED'})

    @mock.patch.object(Client, '_call')
    def test_not_preapproval_key(self, _call):
        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
        self.paypal.get_pay_key(*self.data)
        assert 'preapprovalKey' not in _call.call_args[0][1]

    @mock.patch.object(Client, '_call')
    def test_preapproval_key(self, _call):
        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
        self.paypal.get_pay_key(*self.data, preapproval='xyz')
        eq_(_call.call_args[0][1]['preapprovalKey'], 'xyz')

    @mock.patch.object(Client, '_call')
    def test_usd_default(self, _call):
        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
        self.paypal.get_pay_key(*self.data)
        eq_(_call.call_args[0][1]['currencyCode'], 'USD')

    @mock.patch.object(Client, '_call')
    def test_other_currency(self, _call):
        _call.return_value = {'payKey': '123', 'paymentExecStatus': ''}
        self.paypal.get_pay_key(*self.data, currency='EUR')
        eq_(_call.call_args[0][1]['currencyCode'], 'EUR')

    def test_error_currency_junk(self):
        for v in [u'\u30ec\u30b9', 'xysxdfsfd', '¹'.decode('utf8')]:
            self.assertRaises(PaypalDataError,
                              self.paypal.receivers,
                              [], 'f@foo.com', v, '')

other_error = ('error(0).errorId=520001&error(0).message=Foo')


class TestCall(BaseCase):

    def test_no_url(self):
        with self.assertRaises(KeyError):
            self.paypal.call('foo', {})

    @mock.patch('requests.post')
    def test_auth_fails(self, post):
        post.side_effect = AuthError
        with self.assertRaises(AuthError):
            self.paypal.call('get-pay-key', {})

    @mock.patch('requests.post')
    def test_other_fails(self, post):
        post.side_effect = ZeroDivisionError
        with self.assertRaises(PaypalError):
            self.paypal.call('get-pay-key', {})

    @mock.patch('requests.post')
    def test_error_raised(self, post):
        post.return_value.text = other_error.replace('520001', '589023')
        try:
            self.paypal.call('get-pay-key', {})
        except PaypalError as error:
            eq_(error.id, '589023')
        else:
            raise ValueError('No PaypalError was raised')

    @mock.patch('requests.post')
    def test_error_one_currency(self, opener):
        opener.return_value.text = other_error.replace('520001', '559044')
        try:
            self.paypal.call('get-pay-key', {'currencyCode': 'BRL'})
        except PaypalError as error:
            eq_(error.id, '559044')
            assert 'Brazilian Real' in str(error)
        else:
            raise ValueError('No PaypalError was raised')

    @mock.patch('requests.post')
    def test_error_no_currency(self, opener):
        opener.return_value.text = other_error.replace('520001', '559044')
        try:
            self.paypal.call('get-pay-key', {})
        except PaypalError as error:
            eq_(error.id, '559044')
        else:
            raise ValueError('No PaypalError was raised')

good_check_purchase = ('status=CREATED')


class TestPurchase(BaseCase):

    @mock.patch('requests.post')
    def test_check_purchase(self, post):
        post.return_value.text = good_check_purchase
        eq_(self.paypal.check_purchase('some-paykey'), {'status': 'CREATED'})

    @mock.patch('requests.post')
    def test_check_purchase_fails(self, post):
        post.return_value.text = other_error
        with self.assertRaises(PaypalError):
            self.paypal.check_purchase('some-paykey')

good_personal_basic = {
        'response.personalData(0).personalDataKey':
            'http://axschema.org/contact/country/home',
        'response.personalData(0).personalDataValue': 'US',
        'response.personalData(1).personalDataValue': 'batman@gmail.com',
        'response.personalData(1).personalDataKey':
            'http://axschema.org/contact/email',
        'response.personalData(2).personalDataValue': 'man'}

good_personal_advanced = {
        'response.personalData(0).personalDataKey':
            'http://schema.openid.net/contact/street1',
        'response.personalData(0).personalDataValue': '1 Main St',
        'response.personalData(1).personalDataKey':
            'http://schema.openid.net/contact/street2',
        'response.personalData(2).personalDataValue': 'San Jose',
        'response.personalData(2).personalDataKey':
            'http://axschema.org/contact/city/home'}


@mock.patch.object(Client, '_call')
class TestPersonalLookup(BaseCase):

    def setUp(self):
        super(TestPersonalLookup, self).setUp()
        self.data = {'GetBasicPersonalData': good_personal_basic,
                     'GetAdvancedPersonalData': good_personal_advanced}

    def test_personal_works(self, _call):
        _call.return_value = good_personal_basic
        eq_(self.paypal.get_personal_basic('foo')['email'], 'batman@gmail.com')

    def test_personal_absent(self, _call):
        _call.return_value = good_personal_basic
        eq_(self.paypal.get_personal_basic('foo').get('last_name'), None)

    def test_personal_advanced(self, _call):
        _call.return_value = good_personal_advanced
        eq_(self.paypal.get_personal_basic('foo')['address_one'], '1 Main St')

    def test_personal_unicode(self, _call):
        personal = good_personal_basic.copy()
        value = u'Österreich'
        personal['response.personalData(1).personalDataValue'] = value
        _call.return_value = personal
        eq_(self.paypal.get_personal_basic('foo')['email'], value)


@mock.patch('requests.post')
@mock.patch.object(settings, 'PAYPAL_AUTH',
                   {'USER': 'a', 'PASSWORD': 'b', 'SIGNATURE': 'c'})
class TestAuthWithToken(BaseCase):

    def test_token_header(self, opener):
        opener.return_value.text = good_response
        self.paypal._call('http://some.url', {}, auth_token=good_token)
        assert 'X-PAYPAL-AUTHORIZATION' in opener.call_args[1]['headers']

    def test_normal_header(self, opener):
        opener.return_value.text = good_response
        self.paypal._call('http://some.url', {})
        assert 'X-PAYPAL-SECURITY-PASSWORD' in opener.call_args[1]['headers']

good_refund = {
    'refundInfoList.refundInfo(0).receiver.email': 'bob@example.com',
    'refundInfoList.refundInfo(0).refundFeeAmount': '1.03',
    'refundInfoList.refundInfo(0).refundGrossAmount': '123.45',
    'refundInfoList.refundInfo(0).refundNetAmount': '122.42',
    'refundInfoList.refundInfo(0).refundStatus': 'REFUNDED_PENDING',
    'refundInfoList.refundInfo(1).receiver.amount': '1.23',
    'refundInfoList.refundInfo(1).receiver.email': 'apps@mozilla.com',
    'refundInfoList.refundInfo(1).refundFeeAmount': '0.02',
    'refundInfoList.refundInfo(1).refundGrossAmount': '1.23',
    'refundInfoList.refundInfo(1).refundNetAmount': '1.21',
    'refundInfoList.refundInfo(1).refundStatus': 'REFUNDED'}

no_token_refund = {
    'refundInfoList.refundInfo(0).receiver.amount': '123.45',
    'refundInfoList.refundInfo(0).receiver.email': 'bob@example.com',
    'refundInfoList.refundInfo(0).refundStatus': 'NO_API_ACCESS_TO_RECEIVER'}

processing_failed_refund = {
    'refundInfoList.refundInfo(0).receiver.email': 'seller__biz@gmail.com',
    'refundInfoList.refundInfo(0).refundStatus': 'NOT_PROCESSED',
    'refundInfoList.refundInfo(1).receiver.amount': '0.30',
    'refundInfoList.refundInfo(1).receiver.email': 'andy__biz@gmail.com',
    'refundInfoList.refundInfo(1).refundStatus': 'NO_API_ACCESS_TO_RECEIVER'}

error_refund = {
    'refundInfoList.refundInfo(0).receiver.amount': '123.45',
    'refundInfoList.refundInfo(0).receiver.email': 'bob@example.com',
    'refundInfoList.refundInfo(0).refundStatus': 'REFUND_ERROR'}

already_refunded = {
    'refundInfoList.refundInfo(0).receiver.amount': '123.45',
    'refundInfoList.refundInfo(0).receiver.email': 'bob@example.com',
    'refundInfoList.refundInfo(0).refundStatus':
        'ALREADY_REVERSED_OR_REFUNDED'}


@mock.patch.object(Client, '_call')
class TestRefund(BaseCase):

    def test_refund_success(self, _call):
        _call.return_value = good_refund
        data = self.paypal.get_refund('fake-paykey')
        eq_(data[0]['refundFeeAmount'], '1.03')
        eq_(data[1]['refundFeeAmount'], '0.02')

    def test_refund_no_refund_token(self, _call):
        _call.return_value = no_token_refund
        eq_(self.paypal.get_refund('fake-paykey')[0]['refundStatus'],
            'NO_API_ACCESS_TO_RECEIVER')

    def test_refund_processing_failed(self, _call):
        _call.return_value = processing_failed_refund
        eq_(self.paypal.get_refund('fake-paykey')[0]['refundStatus'],
            'NO_API_ACCESS_TO_RECEIVER')

    def test_refund_wrong_status(self, _call):
        _call.return_value = error_refund
        with self.assertRaises(PaypalError):
            self.paypal.get_refund('fake-paykey')

    def test_refunded_already(self, _call):
        _call.return_value = already_refunded
        eq_(self.paypal.get_refund('fake-paykey')[0]['refundStatus'],
            'ALREADY_REVERSED_OR_REFUNDED')
