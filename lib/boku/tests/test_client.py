import time
import urlparse
from decimal import Decimal

from django import test
from django.core.exceptions import ImproperlyConfigured

import mock
from nose.tools import assert_raises, eq_, ok_, raises

from lib.boku.client import (get_boku_request_signature, get_client,
                             BokuClient, BokuException, MockClient,
                             ProxyClient)
from lib.boku.tests import sample_xml


class BokuClientTests(test.TestCase):

    def setUp(self):
        self.merchant_id = 'merchant_id'
        self.secret_key = 'secret_key'
        self.client = BokuClient(self.merchant_id, self.secret_key)
        self.patched_get = mock.patch('requests.get')
        self.mock_get = self.patched_get.start()
        self.addCleanup(self.patched_get.stop)

    def start_transaction(self, service_id='service id',
                          consumer_id='consumer', price=Decimal('15.00'),
                          external_id='external id', currency='MXN',
                          callback_url='http://test/',
                          forward_url='http://test/success',
                          product_name='Django Pony',
                          country='MX'):
        return self.client.start_transaction(service_id=service_id,
                                             consumer_id=consumer_id,
                                             price=price,
                                             currency=currency,
                                             external_id=external_id,
                                             callback_url=callback_url,
                                             forward_url=forward_url,
                                             product_name=product_name,
                                             country=country)

    def test_client_uses_signed_request(self):
        params = {
            'merchant-id': self.merchant_id,
            'param': 'value',
            'timestamp': int(time.time()),
        }
        signature = get_boku_request_signature(self.secret_key, params)

        try:
            self.client.api_call('/path', params)
        except:
            pass

        call_url = self.mock_get.call_args[0][0]
        sig_param = 'sig={signature}'.format(signature=signature)
        ok_(sig_param in call_url)

    def test_client_raises_exception_on_non_200_http_response(self):
        response = mock.Mock()
        response.status_code = 400
        self.mock_get.return_value = response

        with assert_raises(BokuException) as context:
            self.client.api_call('/path', {})

        eq_(context.exception.message, 'Request Failed: 400')

    def test_client_raises_exception_on_invalid_xml(self):
        response = mock.Mock()
        response.status_code = 200
        response.content = '<invalid xml'
        self.mock_get.return_value = response

        with assert_raises(BokuException) as context:
            self.client.api_call('/path', {})

        ok_(
            'XML Parse Error' in context.exception.message,
            'XML Parse Error not found in {message}'.format(
                message=context.exception.message
            )
        )

    def test_client_raises_exception_when_response_code_not_present(self):
        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.empty
        self.mock_get.return_value = response

        with assert_raises(BokuException) as context:
            self.client.api_call('/path', {})

        eq_(
            context.exception.message,
            'Unable to determine API call result code'
        )

    def test_client_raises_exception_on_non_zero_response_code(self):
        result_code = 1
        result_message = 'Failure!'

        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.billing_request.format(
            result_code=result_code,
            result_message=result_message
        )
        self.mock_get.return_value = response

        with assert_raises(BokuException) as context:
            self.client.api_call('/path', {})

        eq_(
            context.exception.message,
            'API Error: {result_code} {result_message}'.format(
                result_code=result_code,
                result_message=result_message
            )
        )
        eq_(context.exception.result_code, result_code)
        eq_(context.exception.result_msg, result_message)

    def test_client_get_pricing_calls_api_with_correct_params(self):
        country = 'CA'

        with mock.patch('lib.boku.client.BokuClient.api_call') as mock_client:
            try:
                self.client.get_pricing(country)
            except BokuException:
                pass

            mock_client.assert_called_with('/billing/request', {
                'action': 'price',
                'country': country,
            })

    def test_client_get_pricing_calls_returns_pricing_json(self):
        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.pricing_request
        self.mock_get.return_value = response

        prices = self.client.get_pricing('CA', currency='CDN')
        eq_(
            prices, [{
                'status': '1',
                'receivable-gross': '465',
                'currency-decimal-places': '2',
                'reference-amount': '115',
                'exchange': '13.01193',
                'currency-symbol-orientation': 'l',
                'country': 'CA',
                'display-price': '$15.00',
                'reference-receivable-gross': '36',
                'reference-receivable-net': '32',
                'price-ex-salestax': '1293',
                'currency': 'CDN',
                'amount': '1500',
                'reference-price-inc-salestax': '115',
                'currency-symbol': '$',
                'price-inc-salestax': '1500',
                'reference-price-ex-salestax': '99',
                'receivable-net': '419',
                'number-billed-messages': '1'
            }]
        )

    def test_client_get_price_rows_returns_row_ref(self):
        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.pricing_request
        self.mock_get.return_value = response

        price_rows = self.client.get_price_rows('CA')
        eq_(price_rows[Decimal('15.00')], 0)

    def test_client_start_transaction_calls_api_with_correct_params(self):
        service_id = 'service id'
        consumer_id = 'consumer'
        currency = 'MXN'
        price = Decimal('15.00')
        external_id = 'external id'
        callback_url = 'http://test/'
        forward_url = 'http://test/success'
        product_name = 'Unicorn Dust'
        country = 'MX'

        with mock.patch('lib.boku.client.BokuClient.api_call') as mock_client:
            try:
                self.start_transaction(
                    callback_url=callback_url,
                    forward_url=forward_url,
                    consumer_id=consumer_id,
                    external_id=external_id,
                    currency=currency,
                    price=price,
                    product_name=product_name,
                    service_id=service_id,
                    country=country,
                )
            except BokuException:
                pass

            mock_client.assert_called_with('/billing/request', {
                'action': 'prepare',
                'callback-url': callback_url,
                'fwdurl': forward_url,
                'consumer-id': consumer_id,
                'param': external_id,
                'desc': product_name,
                'sub-merchant-name': 'Marketplace',
                'price-inc-salestax': 1500,
                'currency': currency,
                'service-id': service_id,
                'country': country,
            })

    def test_long_product_names(self):
        product_name = u'Unicorn Dust From A Majestic \u2603'

        with mock.patch('lib.boku.client.BokuClient.api_call') as mock_client:
            self.start_transaction(product_name=product_name)
            # The name is not truncated by us but we issue some log warnings.
            # This covers some code to make sure there are no exceptions.
            eq_(mock_client.call_args[0][1]['desc'], 'Unicorn Dust From A ')

    def test_non_ascii_names(self):
        product_name = u'Ivan Krsti\u0107'

        with mock.patch('lib.boku.client.BokuClient.api_call') as mock_client:
            self.start_transaction(product_name=product_name)
            eq_(mock_client.call_args[0][1]['desc'], product_name)

    def test_client_start_transaction_returns_start_transaction_json(self):
        transaction_id = 'abc123'
        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.prepare_request.format(
            transaction_id=transaction_id
        )
        self.mock_get.return_value = response

        transaction = self.start_transaction()
        eq_(
            transaction, {
                'buy_url': 'http://example_buy_url/',
                'transaction_id': transaction_id,
            }
        )

    def test_client_check_transaction_calls_api_with_correct_params(self):
        transaction_id = 'abc123'

        with mock.patch('lib.boku.client.BokuClient.api_call') as mock_client:
            try:
                self.client.check_transaction(transaction_id)
            except Exception:
                pass

            mock_client.assert_called_with('/billing/request', {
                'action': 'verify-trx-id',
                'trx-id': transaction_id,
            })

    def test_client_check_transaction_returns_check_transaction_json(self):
        transaction_id = 'abc123'
        amount = 100

        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.transaction_request.format(
            transaction_id=transaction_id
        )
        self.mock_get.return_value = response

        transaction = self.client.check_transaction(transaction_id)
        eq_(transaction, {'amount': amount, 'paid': amount})


class TestClient(test.TestCase):

    def test_mock(self):
        assert isinstance(get_client('', ''), MockClient)

    def test_proxy(self):
        with self.settings(BOKU_MOCK=False, BOKU_PROXY='blah'):
            assert isinstance(get_client('', ''), ProxyClient)

    def test_real(self):
        with self.settings(BOKU_MOCK=False, BOKU_PROXY='',
                           BOKU_SECRET_KEY='f'):
            assert isinstance(get_client('', ''), BokuClient)

    @raises(ImproperlyConfigured)
    def test_nope(self):
        with self.settings(BOKU_MOCK=False, BOKU_PROXY='',
                           BOKU_SECRET_KEY=''):
            get_client('', '')


class TestProxy(test.TestCase):

    def setUp(self):
        self.merchant_id = 'merchant_id'
        self.secret_key = 'secret_key'
        self.client = ProxyClient(self.merchant_id, self.secret_key)
        self.patched_get = mock.patch('requests.get')
        self.mock_get = self.patched_get.start()
        self.addCleanup(self.patched_get.stop)

        self.transaction_id = 'abc123'

        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.transaction_request.format(
            transaction_id=self.transaction_id
        )
        self.mock_get.return_value = response

    def test_good(self):
        # A copy of
        # test_client_check_transaction_returns_check_transaction_json
        # to prove that everything went through successfully.
        amount = 100

        with self.settings(BOKU_PROXY='https://some.proxy/foo/'):
            transaction = self.client.check_transaction(self.transaction_id)

        eq_(transaction, {'amount': amount, 'paid': amount})

        # The only difference is here, we test it went it to the proxy.
        url = urlparse.urlparse(self.mock_get.call_args_list[0][0][0])
        eq_(url.netloc, 'some.proxy')
        eq_(url.path, '/foo/boku/billing/request')

    def test_no_trailing_slash(self):
        # Same as above, but without the trailing slash on the URL.
        with self.settings(BOKU_PROXY='https://some.proxy/foo'):
            self.client.check_transaction(self.transaction_id)

        url = urlparse.urlparse(self.mock_get.call_args_list[0][0][0])
        eq_(url.path, '/foo/boku/billing/request')
