import calendar
import hashlib
import time
import urllib
from collections import namedtuple
from decimal import Decimal
from itertools import chain
from urlparse import parse_qs, urlparse, urlunparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property

import lxml
import requests
from django_statsd.clients import statsd
from slumber import url_join

from lib.boku import constants
from lib.boku.errors import BokuException, SignatureError
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
    if not secret_key:
        raise ImproperlyConfigured('BOKU_SECRET_KEY not set')

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

    def _sign(self, params):
        params['merchant-id'] = self.merchant_id
        params['sig'] = get_boku_request_signature(self.secret_key, params)
        return params

    def api_call(self, path, params, add_timestamp=True):
        if add_timestamp and 'timestamp' not in params:
            params['timestamp'] = str(calendar.timegm(time.gmtime()))

        self._sign(params)
        url = '{domain}{path}?{params}'.format(
            domain=settings.BOKU_API_DOMAIN,
            path=path,
            params=urllib.urlencode(params)
        )

        response = self._get(url)
        if response.status_code == 204:
            # No point in trying parse the body of 204 responses.
            assert not response.content, (
                'Response with status: 204, body must be empty')
            log.warning('Not parsing empty body, status: 204')
            return

        # Handle an http request failure.
        if response.status_code != 200:
            log.error('Boku API bad status: {url} {status} {content}'.format(
                url=url,
                status=response.status_code,
                content=response.content,
            ))
            raise BokuException(
                'Request Failed: {status}'.format(status=response.status_code),
                status=response.status_code
            )

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

        for row_ref, price_row in enumerate(pricing):
            decimal_places = int(price_row['currency-decimal-places'])
            price_amount = int(price_row['price-inc-salestax'])
            price_decimal = Decimal(price_amount) / (10 ** decimal_places)
            # Row-ref numbers are 0-based.
            price_rows[price_decimal] = row_ref
            log.info('Boku price {price} is row-ref {row_ref}; '
                     'currency={cur}; country={country}; status={status}'
                     .format(price=price_decimal,
                             row_ref=price_rows[price_decimal],
                             cur=currency, country=country,
                             status=price_row['status']))
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
                          external_id, price, currency, service_id,
                          forward_url, country, product_name):
        """
        Begin a transaction with Boku.

        Parameters:

        :param callback_url: A URL that Boku notifies when transaction is
                             complete.
        :param forward_url: A url to redirect to after successful/failed
                            payment.
        :param consumer_id: A unique string identifier for the purchaser.
        :param external_id: A unique string identifier for the transaction.
        :param price: The price as a decimal such as Decimal('15.00').
        :param currency: Abbreviated currency code such as MXN.
        :param service_id: The Boku ID (integer) for the service being sold.
        :param country: The ISO 3166-1-alpha-2 country code that they
                        buyer is in.
        :param product_name: The name of the item being purchased.
        """
        if currency not in constants.DECIMAL_PLACES:
            raise KeyError(
                'No multiplier to figure out decimal places for currency {c}'
                .format(c=currency))
        price = int(price * constants.DECIMAL_PLACES[currency])

        if len(product_name) > 20:
            log.warning(u'Truncating product name for Boku: {n}. '
                        u'Transaction: {t}'.format(n=product_name,
                                                   t=external_id))
            product_name = product_name[0:20]

        tree = self.api_call('/billing/request', {
            'action': 'prepare',
            'callback-url': callback_url,
            'fwdurl': forward_url,
            'consumer-id': consumer_id,
            'param': external_id,
            # This is the merchant name that will show up on the Boku form.
            # It must be shorter than 15 characters.
            'sub-merchant-name': 'Marketplace',
            'desc': product_name,
            'currency': currency,
            'price-inc-salestax': price,
            'service-id': service_id,
            'country': country,
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

    def check_sig(self, *args, **kw):
        """
        Not checking the signature unless you are in a proxy.
        """
        log.info('Not checking the Boku signature locally.')


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

    """
    A client, that instead of speaking to Boku directly, sends requests to
    the solitude proxy. The solitude proxy will sign the actual request and
    send it on to Boku.
    """

    def _sign(self, params):
        # Don't do any signing, the proxy will do that.
        return params

    def _get(self, url):
        # Strip the boku part out of the URL and insert the proxy instead.
        url = urlunparse(('', '') + urlparse(url)[2:])
        # url_join takes care of missing or extra / in urls, but we must strip
        # the first / off the url above.
        proxy = url_join(settings.BOKU_PROXY, 'boku', url[1:])

        # Now continue as normal, call the proxy.
        log.info('Boku proxy client call: {url}'.format(url=proxy))
        with statsd.timer('solitude.boku.api'):
            return requests.get(proxy)

    def check_sig(self, data):
        """
        Check that a signature is valid. This check has to be done on the
        proxy, because the solitude database does not have access to the
        required BOKU_SECRET_KEY.
        """
        try:
            self.api_call('/check_sig', data, add_timestamp=False)
        except BokuException as e:
            # If the signature check failed, a 400 is raised.
            if e.status == 400:
                raise SignatureError('sig verification failed')
            # Re-raise any other error since we aren't sure what it is.
            raise


def get_client(*args):
    """
    Use this to get the right client and communicate with Boku.
    """
    if settings.BOKU_MOCK:
        log.warning('Boku is using the mock client')
        return MockClient(*args)

    if settings.BOKU_PROXY:
        return ProxyClient(*args)

    if not settings.BOKU_SECRET_KEY:
        raise ImproperlyConfigured('Boku secret key is blank, configure '
                                   'your BOKU_SECRET_KEY setting.')

    return BokuClient(*args)


class BokuClientMixin(object):

    @cached_property
    def boku_client(self):
        return get_client(
            settings.BOKU_MERCHANT_ID,
            settings.BOKU_SECRET_KEY
        )
