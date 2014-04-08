import calendar
import hashlib
import time
import urllib
from decimal import Decimal
from itertools import chain

from django.conf import settings

import lxml
import requests
from django_statsd.clients import statsd

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


class BokuException(Exception):

    def __init__(self, message, result_code=None, result_msg=None):
        super(BokuException, self).__init__(message)
        self.result_code = result_code
        self.result_msg = result_msg


class BokuClient(object):

    def __init__(self, merchant_id, secret_key):
        self.merchant_id = merchant_id
        self.secret_key = secret_key

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

        log.info('Boku client call: {url}'.format(url=url))
        with statsd.timer('solitude.boku.api'):
            response = requests.get(url)

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

    def start_transaction(self, service_id, consumer_id,
                          price_row, external_id):
        """
        Begin a transaction with Boku.

        Parameters:

            service_id - <str> The Boku ID for the service being sold
            consumer_id - <str> A unique identifier for the purchaser
            price_row - <int> The price row for a given amount
                              can be found in get_pricing()
            external_id - <str> A unique identifier for the transaction
        """
        tree = self.api_call('/billing/request', {
            'action': 'prepare',
            'param': external_id,
            'consumer-id': consumer_id,
            'row-ref': price_row,
            'service-id': service_id,
        })

        return {
            'button_markup': tree.find('button-markup').text,
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
