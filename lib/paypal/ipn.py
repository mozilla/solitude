from decimal import Decimal
import re
from urlparse import parse_qsl

from django.conf import settings

import commonware.log
from django_statsd.clients import statsd
import requests

from lib.paypal import constants
from lib.paypal.urls import urls
from lib.transactions.models import utils

log = commonware.log.getLogger('s.paypal')


number_re = re.compile('transaction\[(?P<number>\d+)\]\.(?P<name>\w+)')
currency_re = re.compile('(?P<currency>\w+) (?P<amount>[\d.,]+)')


class IPN(object):
    # A special class for handling incoming IPN data.

    def __init__(self, raw):
        self.raw = raw
        self.raw_dict = dict(parse_qsl(raw))
        self.parsed = {}
        self.status = None
        self.action = None

    def is_valid(self):
        if self.raw_dict['payment_status'].lower() != 'completed':
            log.info('Payment status not completed.')
            return False

        url = urls['ipn']
        data = u'cmd=_notify-validate&' + self.raw
        with statsd.timer('solitude.paypal.ipn.validate'):
            log.info('Calling paypal for verification of ipn.')
            response = requests.post(url, data, cert=settings.PAYPAL_CERT,
                                     verify=True)

        if response.text != 'VERIFIED':
            log.info('Verification failed.')

        return True

    def parse(self):
        transactions = {}
        for k, v in self.parsed.items():
            match = number_re.match(k)
            if match:
                data = match.groupdict()
                transactions.setdefault(data['number'], {})
                if data['name'] == 'amount':
                    res = currency_re.match(v).groupdict()
                    if 'amount' in res:
                        v = Decimal(res['amount'])

                transactions[data['number']][data['name']] = v

        return transactions

    def process(self):
        if not self.is_valid():
            log.info('Not a valid IPN call.')
            self.status = constants.IPN_STATUS_IGNORED
            return

        self.parsed = self.parse()

        methods = {'completed': [utils.completed, constants.TYPE_PAYMENT],
                   'refunded': [utils.refunded, constants.TYPE_REFUND],
                   'reversal': [utils.reversal, constants.TYPE_CHARGEBACK]}

        # Ensure that we process 0, then 1 etc.
        for (k, v) in sorted(self.parsed.items()):
            status = v.get('status', '').lower()

            if status not in methods:
                continue

            if utils[status](v[0]):
                self.status = constants.IPN_STATUS_OK
                self.action = v[1]
                # Because of chained payments a refund is more than one
                # transaction. But from our point of view, it's actually
                # only one transaction and
                # we can safely ignore the rest.
                if v[1] == constants.IPN_ACTION_REFUND:
                    break

        # If nothing got processd on this, we ignored it.
        if not self.status:
            self.status = constants.IPN_STATUS_IGNORED
