from lib.transactions import constants
from lib.transactions.models import PaypalTransaction


def completed(detail, item):
    try:
        record = (PaypalTransaction.objects
                                   .get(uuid=detail.get('tracking_id'),
                                        status=constants.STATUS_PENDING))
    except PaypalTransaction.DoesNotExist:
        return False

    record.status = constants.STATUS_COMPLETED
    record.save()
    return True


def refunded(detail, item):
    return refund(detail, item, constants.TYPE_REFUND)


def reversal(detail, item):
    return refund(detail, item, constants.TYPE_REVERSAL)


def refund(detail, item, type_):
    # Check we have this transaction.
    try:
        record = PaypalTransaction.objects.get(uuid=detail['tracking_id'],
                                            status=constants.STATUS_COMPLETED,
                                            type=constants.TYPE_PAYMENT)
    except PaypalTransaction.DoesNotExist:
        return False

    # Check that the transaction has not already been processed.
    try:
        PaypalTransaction.objects.get(related=record)
        return False
    except PaypalTransaction.DoesNotExist:
        pass

    PaypalTransaction.objects.create(
            type=type_, correlation_id=detail.get('correlation_id', ''),
            # The correlation id does not seem to be present on IPN. But if
            # they change their mind, I'll take it.
            pay_key=detail['pay_key'], seller=record.seller,
            amount=item['amount'], currency=item['currency'],
            # TODO(andym): hey what?
            uuid=detail['tracking_id'] + ':refund', related=record)

    # TODO(andym): some CEF logging.
    return True
