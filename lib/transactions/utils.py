from lib.transactions import constants
from lib.transactions.models import PaypalTransaction


def completed(data):
    try:
        record = (PaypalTransaction.objects
                                   .get(uuid=data.get('tracking_id'),
                                        status=constants.STATUS_PENDING))
    except PaypalTransaction.DoesNotExist:
        return False

    record.status = constants.STATUS_COMPLETED
    record.save()
    return True


def refunded(data):
    return refund(data, constants.TYPE_REFUND)


def rejected(data):
    return refund(data, constants.TYPE_REJECTED)


def refund(data, type_):
    # Check we have this transaction.
    try:
        record = PaypalTransaction.objects.get(uuid=data['tracking_id'],
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
            type=type_, correlation_id=data.get('correlation_id', ''),
            # The correlation id does not seem to be present on IPN. But if
            # they change their mind, I'll take it.
            pay_key=data['pay_key'], seller=record.seller,
            amount=data['amount'], currency=data['currency'],
            # TODO(andym): hey what?
            uuid=data['tracking_id'] + ':refund', related=record)

    # TODO(andym): some CEF logging.
    return True


