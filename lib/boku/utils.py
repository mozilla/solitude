from decimal import Decimal

from django.conf import settings

from lib.boku.constants import DECIMAL_PLACES
from lib.boku.client import get_client
from lib.boku.errors import VerificationError

from solitude.logger import getLogger

log = getLogger('s.boku')


def fix_price(amount, currency):
    """
    Convert a Boku amount into a normal solitude value.
    """
    # Because dividing a float would be really bad.
    assert isinstance(amount, Decimal), 'Not a decimal'
    return amount / DECIMAL_PLACES[currency]


def verify(transaction, amount, currency):
    """
    Verify a transaction against Boku.
    """
    def error(msg):
        msg = 'transaction {0}: {1}'.format(transaction, msg)
        log.error(msg)
        raise VerificationError(msg)

    client = get_client(settings.BOKU_MERCHANT_ID, settings.BOKU_SECRET_KEY)
    res = client.check_transaction(transaction)

    try:
        real = fix_price(res['amount'], currency)
    except (KeyError, AssertionError):
        error('not a valid price {0} or currency {1}'
              .format(res['amount'], currency))

    if real != amount:
        error('did not verify: {0} != {1}'.format(real, amount))

    log.info('transaction: {0} verified successfully'.format(transaction))
