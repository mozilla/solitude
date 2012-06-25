from decimal import Decimal
import re
from urlparse import parse_qsl

from django.conf import settings

import commonware.log
from django_statsd.clients import statsd
import requests

from lib.paypal import constants
from lib.paypal.urls import urls
from lib.transactions import utils

log = commonware.log.getLogger('s.paypal')


number_re = re.compile('transaction\[(?P<number>\d+)\]\.(?P<name>\w+)')
currency_re = re.compile('(?P<currency>\w+) (?P<amount>[\d.,]+)')


class IPN(object):
    # A special class for handling incoming IPN data.

    def __init__(self, raw):
        self.raw = raw
        self.raw_dict = dict(parse_qsl(raw))
        self.transaction = {}
        self.details = {}
        self.status = None
        self.action = None

    def is_valid(self):
        if self.raw_dict.get('status', '').lower() != 'completed':
            log.info('Payment status not completed.')
            return False

        url = urls['ipn']
        data = u'cmd=_notify-validate&' + self.raw
        with statsd.timer('solitude.paypal.ipn.validate'):
            log.info('Calling paypal for verification of ipn.')
            #TODO(andym): should be catching all errors here?
            response = requests.post(url, data, cert=settings.PAYPAL_CERT,
                                     verify=True)

        if response.text != 'VERIFIED':
            log.info('Verification failed.')
            #TODO(andym): CEF logging here.
            return False

        return True

    def parse(self):
        transaction, transactions = {}, {}
        for k, v in self.raw_dict.items():
            match = number_re.match(k)
            if match:
                data = match.groupdict()
                transactions.setdefault(data['number'], {})
                if data['name'] == 'amount':
                    v = currency_re.match(v).groupdict()
                    if 'amount' in v:
                        v['amount'] = Decimal(v['amount'])

                transactions[data['number']][data['name']] = v
            else:
                transaction[k] = v

        return transaction, transactions

    def process(self):
        if not self.is_valid():
            log.info('Not a valid IPN call.')
            self.status = constants.IPN_STATUS_IGNORED
            return

        self.transaction, self.details = self.parse()

        methods = {'completed': [utils.completed,
                                 constants.IPN_ACTION_PAYMENT],
                   'refunded': [utils.refunded, constants.IPN_ACTION_REFUND],
                   'reversal': [utils.reversal, constants.IPN_ACTION_REVERSAL]}

        # Ensure that we process 0, then 1 etc.
        for (k, detail) in sorted(self.details.items()):
            status = detail.get('status', '').lower()

            if status not in methods:
                continue

            # Because of chained payments a refund is more than one
            # transaction. But from our point of view, it's actually
            # only one transaction and we can safely ignore the rest.
            if (len(self.details.keys()) > 1 and
                detail.get('is_primary_receiver', 'true') != 'true'):
                continue

            method, result = methods[status]
            if method(self.transaction, detail):
                self.status = constants.IPN_STATUS_OK
                self.action = result

        # If nothing got processd on this, we ignored it.
        if not self.status:
            self.status = constants.IPN_STATUS_IGNORED
