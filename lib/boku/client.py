import calendar
import hashlib
import time
import urllib
from collections import namedtuple
from decimal import Decimal
from itertools import chain
from urlparse import parse_qs, urlparse, urlunparse

from django.conf import settings
from django.utils.functional import cached_property

import lxml
import requests
from django_statsd.clients import statsd

from lib.boku.errors import BokuException
from lib.boku.tests import sample_xml
from solitude.logger import getLogger


log = getLogger('s.boku')


def get_boku_request_signature(secret_key, request_args):
    """
    Given a dictionary of request parameters, generate
    an MD5 signature using a secret key.

    Implementation details can be found here:
    https://merchants.boku.com/white_label/boku
        /doclibrary/BOKU_SecurityImplementation.pdf
    """
    # Sort the pairs by their key name.
    sorted_pairs = sorted(request_args.items())

    # Combine into a single string with no delimiters.
    pairs_string = u''.join(map(
        unicode,
        chain.from_iterable(sorted_pairs)
    ))

    # Append the secret key to the end.
    signature_string = u'{pairs}{secret_key}'.format(
        pairs=pairs_string,
        secret_key=secret_key
    )

    # Run MD5 to get the signature.
    return hashlib.md5(signature_string.encode('utf8')).hexdigest()


class BokuClient(object):

    def __init__(self, merchant_id, secret_key):
        self.merchant_id = merchant_id
        self.secret_key = secret_key

    def _get(self, url):
        log.info('Boku client call: {url}'.format(url=url))
        with statsd.timer('solitude.boku.api'):
            return requests.get(url)

    def api_call(self, path, params):
        if 'timestamp' not in params:
            params['timestamp'] = str(calendar.timegm(time.gmtime()))

        params['merchant-id'] = self.merchant_id
        params['sig'] = get_boku_request_signature(self.secret_key, params)
        url = '{domain}{path}?{params}'.format(
            domain=settings.BOKU_API_DOMAIN,
            path=path,
            params=urllib.urlencode(params)
        )

        response = self._get(url)

        # Handle an http request failure.
        if response.status_code != 200:
            log.error('Boku API bad status: {url} {status} {content}'.format(
                url=url,
                status=response.status_code,
                content=response.content,
            ))
            raise BokuException('Request Failed: {status}'.format(
                status=response.status_code
            ))

        # Handle an XML parse failure.
        try:
            tree = lxml.etree.fromstring(response.content)
        except lxml.etree.XMLSyntaxError, exception:
            log.error('Boku API bad XML: {url} {status} {content}'.format(
                url=url,
                status=response.status_code,
                content=response.content,
            ))
            raise BokuException('XML Parse Error: {exception}'.format(
                exception=exception
            ))

        # Attempt to find the Boku response code.
        result_code = tree.find('result-code')
        if not (result_code is not None and result_code.text.isdigit()):
            log.error(
                'Boku API unable to find result code: '
                '{url} {status} {content}'.format(
                    url=url,
                    status=response.status_code,
                    content=response.content,
                )
            )
            raise BokuException('Unable to determine API call result code')

        # If the result code is non zero, raise an exception.
        result_code = int(result_code.text)
        if result_code != 0:
            result_msg = tree.find('result-msg')
            if result_msg is not None:
                result_msg_text = result_msg.text
            else:
                result_msg_text = 'Unable to find result message.'

            exception_message = 'API Error: {result_code} {result_msg}'.format(
                result_code=result_code,
                result_msg=result_msg_text,
            )
            raise BokuException(
                exception_message,
                result_code=result_code,
                result_msg=result_msg_text,
            )

        return tree

    def get_pricing(self, country, currency=None):
        """
        Given a country code and optionally a currency, retrieve the list
        of supported price points for that country (and currency).

        See Boku Technical documentation for more detail:

        On-Demand Price Points  Request ('price') API Call
        https://merchants.boku.com/white_label/
            boku/doclibrary/Boku_Technical_Reference.pdf
        """
        params = {
            'action': 'price',
            'country': country,
        }

        if currency:
            params['currency'] = currency

        tree = self.api_call('/billing/request', params)

        return [pricing.attrib for pricing in tree.findall('pricing')]

    def get_price_rows(self, country, currency=None):
        """
        Given a country and optionally a currency, retrieve a dictionary
        which maps a price to its associated price row number suitable for
        starting a transaction.
        """
        pricing = self.get_pricing(country, currency=currency)
        price_rows = {}

        for row_num, price_row in enumerate(pricing):
            decimal_places = int(price_row['currency-decimal-places'])
            price_amount = int(price_row['price-inc-salestax'])
            price_decimal = Decimal(price_amount) / (10**decimal_places)
            price_rows[price_decimal] = row_num + 1
        return price_rows

    def get_service_pricing(self, service_id):
        """
        Given a service id, retrieve a list of all of its
        available price tiers and their currencies.

        See Boku Technical documentation for more detail:

        Static  Matrix  Price Request ('service-prices')  API Call
        https://merchants.boku.com/white_label/
            boku/doclibrary/Boku_Technical_Reference.pdf
        """
        params = {
            'action': 'service-prices',
            'service-id': service_id,
        }

        tree = self.api_call('/billing/request', params)

        services = []
        for service_pricing in tree.findall('service'):
            service = dict(service_pricing.attrib)
            service['prices'] = [
                dict(pricing.attrib) for pricing
                in service_pricing.findall('*/pricing')
            ]
            services.append(service)

        return services

    def start_transaction(self, callback_url, consumer_id,
                          external_id, price_row, service_id):
        """
        Begin a transaction with Boku.

        Parameters:

            callback_url - <str> A url to POST the transaction results to.
            consumer_id - <str> A unique identifier for the purchaser.
            external_id - <str> A unique identifier for the transaction.
            price_row - <int> The price row for a given amount
                              can be found in get_pricing().
            service_id - <str> The Boku ID for the service being sold.
        """
        tree = self.api_call('/billing/request', {
            'action': 'prepare',
            'callback-url': callback_url,
            'consumer-id': consumer_id,
            'param': external_id,
            'row-ref': price_row,
            'service-id': service_id,
        })

        return {
            'buy_url': tree.find('buy-url').text,
            'transaction_id': tree.find('trx-id').text,
        }

    def check_transaction(self, transaction_id):
        """
        Check the status of a transaction_id.
        """
        tree = self.api_call('/billing/request', {
            'action': 'verify-trx-id',
            'trx-id': transaction_id,
        })

        return {
            'amount': Decimal(tree.find('amount').text),
            'paid': Decimal(tree.find('paid').text),
        }


mocks = {
    'price': (200, sample_xml.pricing_request),
    'prepare': (200, sample_xml.prepare_request),
    'service-prices': (200, sample_xml.service_prices_request),
    'verify-trx-id': (200, sample_xml.transaction_request),
}


class MockClient(BokuClient):
    """
    A mock client that returns the value of mock, based on the
    action above.
    """

    def _get(self, url):
        lookup = parse_qs(urlparse(url).query)['action'][0]
        MockResult = namedtuple('MockResult', ['status_code', 'content'])
        result = MockResult(*mocks[lookup])
        return result


class ProxyClient(BokuClient):

    def _get(self, url):
        # Strip the boku part out of the URL and insert the proxy instead.
        url = urlunparse(('', '') + urlparse(url)[2:])
        proxy = '{base}boku{url}'.format(base=settings.BOKU_PROXY, url=url)

        # Now continue as normal, call the proxy.
        log.info('Boku proxy client call: {url}'.format(url=proxy))
        with statsd.timer('solitude.boku.api'):
            return requests.get(proxy)


def get_client(*args):
    """
    Use this to get the right client and communicate with Bango.
    """
    if settings.BOKU_MOCK:
        return MockClient(*args)
    if settings.BOKU_PROXY:
        return ProxyClient(*args)
    return BokuClient(*args)


class BokuClientMixin(object):

    @cached_property
    def boku_client(self):
        return get_client(
            settings.BOKU_MERCHANT_ID,
            settings.BOKU_SECRET_KEY
        )
