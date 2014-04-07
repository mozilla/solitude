import time
import urlparse

import mock
import test_utils
from nose.tools import assert_raises, eq_, ok_

from lib.boku.client import (get_boku_request_signature, get_client,
                             BokuClient, BokuException, MockClient,
                             ProxyClient)
from lib.boku.tests import sample_xml


class BokuClientTests(test_utils.TestCase):

    def setUp(self):
        self.merchant_id = 'merchant_id'
        self.secret_key = 'secret_key'
        self.client = BokuClient(self.merchant_id, self.secret_key)
        self.patched_get = mock.patch('requests.get')
        self.mock_get = self.patched_get.start()
        self.addCleanup(self.patched_get.stop)

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

        with mock.patch('lib.boku.client.BokuClient.api_call') as MockClient:
            try:
                self.client.get_pricing(country)
            except BokuException:
                pass

            MockClient.assert_called_with('/billing/request', {
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

    def test_client_start_transaction_calls_api_with_correct_params(self):
        service_id = 'service id'
        consumer_id = 'consumer'
        price_row = 1
        external_id = 'external id'
        callback_url = 'http://test/'

        with mock.patch('lib.boku.client.BokuClient.api_call') as MockClient:
            try:
                self.client.start_transaction(
                    callback_url=callback_url,
                    consumer_id=consumer_id,
                    external_id=external_id,
                    price_row=price_row,
                    service_id=service_id,
                )
            except BokuException:
                pass

            MockClient.assert_called_with('/billing/request', {
                'action': 'prepare',
                'callback-url': callback_url,
                'consumer-id': consumer_id,
                'param': external_id,
                'row-ref': price_row,
                'service-id': service_id,
            })

    def test_client_start_transaction_returns_start_transaction_json(self):
        service_id = 'service id'
        consumer_id = 'consumer'
        price_row = 1
        external_id = 'external id'
        callback_url = 'http://test/'
        transaction_id = 'abc123'

        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.prepare_request.format(
            transaction_id=transaction_id
        )
        self.mock_get.return_value = response

        transaction = self.client.start_transaction(
            callback_url=callback_url,
            consumer_id=consumer_id,
            external_id=external_id,
            price_row=price_row,
            service_id=service_id,
        )
        eq_(
            transaction, {
                'buy_url': 'http://example_buy_url/',
                'transaction_id': transaction_id,
            }
        )

    def test_client_check_transaction_calls_api_with_correct_params(self):
        transaction_id = 'abc123'

        with mock.patch('lib.boku.client.BokuClient.api_call') as MockClient:
            try:
                self.client.check_transaction(transaction_id)
            except Exception:
                pass

            MockClient.assert_called_with('/billing/request', {
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


class TestClient(test_utils.TestCase):

    def test_mock(self):
        assert isinstance(get_client('', ''), MockClient)

    def test_proxy(self):
        with self.settings(BOKU_PROXY='blah', BOKU_MOCK=False):
            assert isinstance(get_client('', ''), ProxyClient)

    def test_real(self):
        with self.settings(BOKU_PROXY='', BOKU_MOCK=False):
            assert isinstance(get_client('', ''), BokuClient)


class TestProxy(test_utils.TestCase):

    def setUp(self):
        self.merchant_id = 'merchant_id'
        self.secret_key = 'secret_key'
        self.client = ProxyClient(self.merchant_id, self.secret_key)
        self.patched_get = mock.patch('requests.get')
        self.mock_get = self.patched_get.start()
        self.addCleanup(self.patched_get.stop)

    def test_good(self):
        # A copy of
        # test_client_check_transaction_returns_check_transaction_json
        # to prove that everything went through successfully.
        transaction_id = 'abc123'
        amount = 100

        response = mock.Mock()
        response.status_code = 200
        response.content = sample_xml.transaction_request.format(
            transaction_id=transaction_id
        )
        self.mock_get.return_value = response

        with self.settings(BOKU_PROXY='https://some.proxy/foo/'):
            transaction = self.client.check_transaction(transaction_id)
        eq_(transaction, {'amount': amount, 'paid': amount})

        # The only difference is here, we test it went it to the proxy.
        url = urlparse.urlparse(self.mock_get.call_args_list[0][0][0])
        eq_(url.netloc, 'some.proxy')
        eq_(url.path, '/foo/boku/billing/request')
