# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal
import urlparse

from django.conf import settings

import test_utils
import mock
from nose.tools import eq_

from ..constants import HEADERS_URL, HEADERS_TOKEN
from ..client import get_client, Client, ClientProxy, ClientMock
from ..errors import AuthError, CurrencyError, PaypalDataError, PaypalError

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


@mock.patch.object(Client, 'call')
@mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
class TestRefundPermissions(BaseCase):

    args = ['http://foo.com', 'foo']

    def test_get_permissions_url(self, call):
        call.return_value = {'token': 'foo'}
        assert 'foo' in self.paypal.get_permission_url(*self.args)['token']

    def test_get_permissions_url_error(self, call):
        with self.assertRaises(ValueError):
            self.paypal.get_permission_url('', [])

    def test_get_permissions_url_scope(self, call):
        call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        self.paypal.get_permission_url(self.args[0], ['REFUND', 'FOO'])
        eq_(call.call_args[0][1]['scope'], ['REFUND', 'FOO'])

    def test_check_permission_fail(self, call):
        call.return_value = {'scope(0)': 'HAM_SANDWICH'}
        eq_(self.paypal.check_permission(good_token, ['REFUND']),
            {'status': False})

    def test_check_permission(self, call):
        call.return_value = {'scope(0)': 'REFUND'}
        eq_(self.paypal.check_permission(good_token, ['REFUND']),
            {'status': True})

    def test_check_permission_error(self, call):
        call.side_effect = PaypalError
        with self.assertRaises(PaypalError):
            self.paypal.check_permission(good_token, ['REFUND'])

    def test_get_permissions_token(self, call):
        call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        eq_(self.paypal.get_permission_token('foo', ''), good_token)

    def test_get_permissions_subset(self, call):
        call.return_value = {'scope(0)': 'REFUND', 'scope(1)': 'HAM'}
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


@mock.patch.object(Client, 'call')
class TestPreApproval(BaseCase):

    def get_data(self):
        return [datetime.today(), datetime.today() + timedelta(days=365),
                'http://foo/return', 'http://foo/cancel']

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
    def test_preapproval_works(self, call):
        call.return_value = good_preapproval_string
        res = self.paypal.get_preapproval_key(*self.get_data())
        eq_(res['key'], 'PA-2L635945UC9045439')

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
    def test_preapproval_amount(self, call):
        call.return_value = good_preapproval_string
        data = self.get_data()
        self.paypal.get_preapproval_key(*data)
        eq_(call.call_args[0][1]['maxTotalAmountOfAllPayments'], '2000')

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
    @mock.patch.object(settings, 'PAYPAL_LIMIT_PREAPPROVAL', True)
    def test_preapproval_limits(self, call):
        call.return_value = good_preapproval_string
        data = self.get_data()
        self.paypal.get_preapproval_key(*data)
        eq_(call.call_args[0][1]['paymentPeriod'], 'DAILY')
        eq_(call.call_args[0][1]['maxAmountPerPayment'], 15)
        eq_(call.call_args[0][1]['maxNumberOfPaymentsPerPeriod'], 15)

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://foo'))
    @mock.patch.object(settings, 'PAYPAL_LIMIT_PREAPPROVAL', False)
    def test_preapproval_not_limits(self, call):
        call.return_value = good_preapproval_string
        data = self.get_data()
        self.paypal.get_preapproval_key(*data)
        for arg in ['paymentPeriod', 'maxAmountPerPayment',
                    'maxNumberOfPaymentsPerPeriod']:
            assert arg not in call.call_args[0][1]

    @mock.patch.object(settings, 'PAYPAL_URL_WHITELIST', ('http://bar'))
    def test_naughty(self, call):
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
        self.return_value = {'payKey': '123', 'paymentExecStatus': '',
                             'responseEnvelope.correlationId': '456'}
        self.data = ['someone@somewhere.com', 10, 'http://foo/i',
                     'http://foo/c', 'http://foo/r']

    @mock.patch.object(Client, 'call')
    def test_dict_no_split(self, call):
        call.return_value = self.return_value
        self.paypal.get_pay_key(*self.data)
        eq_(call.call_args[0][1]['receiverList.receiver(0).amount'], '10')

    @mock.patch.object(Client, 'call')
    @mock.patch.object(settings, 'PAYPAL_CHAINS', ((13.4, 'us@moz.com'),))
    def test_dict_split(self, call):
        call.return_value = self.return_value
        self.paypal.get_pay_key(*self.data)
        eq_(call.call_args[0][1]['receiverList.receiver(0).amount'], '10')
        eq_(call.call_args[0][1]['receiverList.receiver(1).amount'], '1.34')

    @mock.patch('requests.post')
    def test_get_key(self, post):
        post.return_value.text = good_response
        post.return_value.status_code = 200
        eq_(self.paypal.get_pay_key(*self.data, uuid='xyz'),
            {'pay_key': 'AP-9GD76073HJ780401K', 'status': 'CREATED',
             'correlation_id': '7377e6ae1263c', 'uuid': 'xyz'})

    @mock.patch.object(Client, 'call')
    def test_not_preapproval_key(self, call):
        call.return_value = self.return_value
        self.paypal.get_pay_key(*self.data)
        assert 'preapprovalKey' not in call.call_args[0][1]

    @mock.patch.object(Client, 'call')
    def test_preapproval_key(self, call):
        call.return_value = self.return_value
        self.paypal.get_pay_key(*self.data, preapproval='xyz')
        eq_(call.call_args[0][1]['preapprovalKey'], 'xyz')

    @mock.patch.object(Client, 'call')
    def test_usd_default(self, call):
        call.return_value = self.return_value
        self.paypal.get_pay_key(*self.data)
        eq_(call.call_args[0][1]['currencyCode'], 'USD')

    @mock.patch.object(Client, 'call')
    def test_other_currency(self, call):
        call.return_value = self.return_value
        self.paypal.get_pay_key(*self.data, currency='EUR')
        eq_(call.call_args[0][1]['currencyCode'], 'EUR')

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
    def test_not_currency_error_raised(self, post):
        post.return_value.text = other_error.replace('520001', '589023')
        with self.assertRaises(PaypalError):
            self.paypal.call('check-purchase', {})

    @mock.patch('requests.post')
    def test_currency_error_raised(self, post):
        post.return_value.text = other_error.replace('520001', '580027')
        post.return_value.status_code = 200
        with self.assertRaises(CurrencyError):
            self.paypal.call('get-pay-key', {})

    @mock.patch('requests.post')
    def test_error_raised(self, post):
        post.return_value.text = other_error.replace('520001', '589023')
        post.return_value.status_code = 200
        try:
            self.paypal.call('get-pay-key', {})
        except PaypalError as error:
            eq_(error.id, '589023')
        else:
            raise ValueError('No PaypalError was raised')

    @mock.patch('requests.post')
    def test_error_one_currency(self, post):
        error = other_error + '&currencyCode=BRL'
        post.return_value.text = error.replace('520001', '580027')
        post.return_value.status_code = 200
        try:
            self.paypal.call('get-pay-key', {})
        except PaypalError as error:
            eq_(error.id, '580027')
            assert 'Brazilian Real' in str(error)
        else:
            raise ValueError('No PaypalError was raised')

    @mock.patch('requests.post')
    def test_error_no_currency(self, post):
        post.return_value.text = other_error.replace('520001', '559044')
        post.return_value.status_code = 200
        try:
            self.paypal.call('get-pay-key', {})
        except PaypalError as error:
            eq_(error.id, '559044')
        else:
            raise ValueError('No PaypalError was raised')

    @mock.patch('requests.post')
    def test_http_error(self, post):
        post.return_value.status_code = 500
        with self.assertRaises(PaypalError):
            self.paypal.call('get-pay-key', {})

    def test_error(self):
        res = self.paypal.error(dict(urlparse.parse_qsl(other_error)), {})
        assert isinstance(res, PaypalError)


good_check_purchase = ('status=CREATED')


class TestPurchase(BaseCase):

    @mock.patch('requests.post')
    def test_check_purchase(self, post):
        post.return_value.text = good_check_purchase
        post.return_value.status_code = 200
        eq_(self.paypal.check_purchase('some-paykey'),
            {'status': 'CREATED', 'pay_key': 'some-paykey'})

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


@mock.patch.object(Client, 'call')
class TestPersonalLookup(BaseCase):

    def setUp(self):
        super(TestPersonalLookup, self).setUp()
        self.data = {'GetBasicPersonalData': good_personal_basic,
                     'GetAdvancedPersonalData': good_personal_advanced}

    def test_personal_works(self, call):
        call.return_value = good_personal_basic
        eq_(self.paypal.get_personal_basic('foo')['email'], 'batman@gmail.com')
        eq_(call.call_args[1]['auth_token'], 'foo')

    def test_personal_absent(self, call):
        call.return_value = good_personal_basic
        eq_(self.paypal.get_personal_basic('foo').get('last_name'), None)

    def test_personal_advanced(self, call):
        call.return_value = good_personal_advanced
        eq_(self.paypal.get_personal_basic('foo')['address_one'], '1 Main St')

    def test_personal_unicode(self, call):
        personal = good_personal_basic.copy()
        value = u'Österreich'
        personal['response.personalData(1).personalDataValue'] = value
        call.return_value = personal
        eq_(self.paypal.get_personal_basic('foo')['email'], value)


@mock.patch.object(settings, 'PAYPAL_AUTH',
                   {'USER': 'a', 'PASSWORD': 'b', 'SIGNATURE': 'c'})
class TestAuthWithToken(BaseCase):

    def test_token_header(self):
        assert 'X-PAYPAL-AUTHORIZATION' in (
               self.paypal.headers('http://some.url', auth_token=good_token))

    def test_normal_header(self):
        assert 'X-PAYPAL-SECURITY-PASSWORD' in (
               self.paypal.headers('http://some.url'))

    @mock.patch('requests.post')
    def test_token_call(self, post):
        post.return_value.text = 'some-text'
        post.return_value.status_code = 200
        self.paypal.call('get-pay-key', {}, auth_token=good_token)
        assert 'X-PAYPAL-AUTHORIZATION' in post.call_args[1]['headers']

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
        eq_(data['response'][0]['refundFeeAmount'], '1.03')
        eq_(data['response'][1]['refundFeeAmount'], '0.02')

    def test_refund_no_refund_token(self, _call):
        _call.return_value = no_token_refund
        eq_(self.paypal
                .get_refund('fake-paykey')['response'][0]['refundStatus'],
            'NO_API_ACCESS_TO_RECEIVER')

    def test_refund_processing_failed(self, _call):
        _call.return_value = processing_failed_refund
        eq_(self.paypal
                .get_refund('fake-paykey')['response'][0]['refundStatus'],
            'NO_API_ACCESS_TO_RECEIVER')

    def test_refund_wrong_status(self, _call):
        _call.return_value = error_refund
        with self.assertRaises(PaypalError):
            self.paypal.get_refund('fake-paykey')

    def test_refunded_already(self, _call):
        _call.return_value = already_refunded
        eq_(self.paypal
                .get_refund('fake-paykey')['response'][0]['refundStatus'],
            'ALREADY_REVERSED_OR_REFUNDED')

# These are truncated.
personal = {
    'responseEnvelope.ack': u'Success',
    'userInfo.accountType': u'PERSONAL'
}

business = {
    'responseEnvelope.ack': u'Success',
    'userInfo.accountType': u'BUSINESS'
}


@mock.patch.object(Client, '_call')
class TestVerified(BaseCase):

    def test_personal(self, _call):
        _call.return_value = personal
        eq_(self.paypal.get_verified('a@pers.com')['type'], u'PERSONAL')

    def test_business(self, _call):
        _call.return_value = business
        eq_(self.paypal.get_verified('a@bizs.com')['type'], u'BUSINESS')

    def test_nope(self, _call):
        _call.side_effect = PaypalError
        with self.assertRaises(PaypalError):
            self.paypal.get_verified('nope')


class TestRightClient(test_utils.TestCase):

    def test_no_proxy(self):
        with self.settings(PAYPAL_PROXY=None, SOLITUDE_PROXY=False):
            assert isinstance(get_client(), Client)
            assert get_client().check_personal_email == True

    def test_using_proxy(self):
        with self.settings(PAYPAL_PROXY='http://foo.com'):
            assert isinstance(get_client(), ClientProxy)

    def test_am_proxy(self):
        with self.settings(PAYPAL_PROXY='http://foo.com', SOLITUDE_PROXY=True):
            assert isinstance(get_client(), Client)

    def test_mock(self):
        with self.settings(PAYPAL_MOCK=True):
            assert isinstance(get_client(), ClientMock)
            assert get_client().check_personal_email == False


class TestMock(test_utils.TestCase):

    def setUp(self):
        self.paypal = ClientMock()
        self.url = 'http://foo'

    def test_call_pay_key(self):
        res = self.paypal.call('get-pay-key', {})
        assert res['payKey'].startswith('payKey')

    def test_error(self):
        with self.assertRaises(NotImplementedError):
            self.paypal.call('nope', {})

    def test_preapproval_local(self):
        res = self.paypal.get_preapproval_key('blah', 'blah', self.url, 'blah')
        eq_(res['paypal_url'], self.url)

    def test_preapproval_local(self):
        res = self.paypal.get_permission_url(self.url, 'blah')
        assert res['token'].startswith(self.url)


class TestProxy(test_utils.TestCase):

    def setUp(self):
        self.paypal = ClientProxy()
        self.url = 'http://foo.com'

    def test_headers(self):
        res = self.paypal.headers(self.url, None)
        eq_(res[HEADERS_URL], self.url)
        res = self.paypal.headers(self.url, {'foo': 'bar'})
        eq_(dict(urlparse.parse_qsl(res[HEADERS_TOKEN]))['foo'], 'bar')

    @mock.patch.object(ClientProxy, '_call')
    def test_call(self, _call):
        with self.settings(PAYPAL_PROXY=self.url):
            self.paypal.call('get-pay-key', {'foo': 'bar'})
        args = _call.call_args
        eq_(args[0][0], self.url)
        eq_(args[0][1], u'foo=bar&requestEnvelope.errorLanguage=en_US')
        eq_(args[0][2]['X_SOLITUDE_URL'], 'get-pay-key')

    @mock.patch.object(ClientProxy, '_call')
    def test_call_with_token(self, _call):
        with self.settings(PAYPAL_PROXY=self.url):
            self.paypal.call('get-pay-key', {'foo': 'bar'},
                             auth_token={'token': 'token'})
        args = _call.call_args
        eq_(args[0][0], self.url)
        eq_(args[0][2]['X_SOLITUDE_TOKEN'], 'token=token')
