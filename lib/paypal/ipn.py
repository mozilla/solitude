from decimal import Decimal
import re
from urlparse import parse_qsl

from lib.paypal import constants
from lib.paypal.client import get_client
from lib.transactions import utils

from solitude.logger import getLogger

log = getLogger('s.paypal')


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
        self.client = get_client()

    def is_valid(self):
        if self.raw_dict.get('status', '').lower() != 'completed':
            log.info('Payment status not completed.')
            return False

        return self.client.get_ipn_verify(self.raw)

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
            res = method(self.transaction, detail)
            log.info('Processing using %s returned %s' % (status, bool(res)))
            if res:
                self.status = constants.IPN_STATUS_OK
                self.action = result
                self.detail = detail
                # We should only ever be processing one value, because of
                # chained payments, we should stop here.
                break

        # If nothing got processd on this, we ignored it.
        if not self.status:
            log.info('Not processed, set state to ignored')
            self.status = constants.IPN_STATUS_IGNORED
