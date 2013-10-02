from lib.transactions import constants
from lib.transactions.models import Transaction

from solitude.logger import getLogger

log = getLogger('s.transactions')


def completed(detail, item):
    log.info('Completing transaction.')
    try:
        record = (Transaction.objects
                                   .get(uuid=detail.get('tracking_id'),
                                        status__in=(constants.STATUS_PENDING,
                                                    constants.STATUS_CHECKED)))
    except Transaction.DoesNotExist:
        return False

    record.status = constants.STATUS_COMPLETED
    record.save()
    return True


def refunded(detail, item):
    log.info('Refunding transaction.')
    return refund(detail, item, constants.TYPE_REFUND)


def reversal(detail, item):
    log.info('Reversing transaction.')
    return refund(detail, item, constants.TYPE_REVERSAL)


def refund(detail, item, type_):
    # Check we have this transaction.
    try:
        record = Transaction.objects.get(uuid=detail['tracking_id'],
                                         status=constants.STATUS_COMPLETED,
                                         type=constants.TYPE_PAYMENT)
    except Transaction.DoesNotExist:
        return False

    # Check that the transaction has not already been processed.
    try:
        Transaction.objects.get(related=record)
        return False
    except Transaction.DoesNotExist:
        pass

    Transaction.objects.create(
            type=type_,
            uid_support=detail.get('correlation_id', ''),
            # The correlation id does not seem to be present on IPN. But if
            # they change their mind, I'll take it.
            uid_pay=detail['pay_key'],
            seller_product=record.seller_product,
            amount=-item['amount']['amount'],
            currency=item['amount']['currency'],
            provider=constants.PROVIDER_PAYPAL,
            # TODO(andym): hey what?
            uuid=detail['tracking_id'] + ':refund',
            related=record)

    # TODO(andym): some CEF logging.
    return True
