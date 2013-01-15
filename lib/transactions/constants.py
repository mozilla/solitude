STATUS_PENDING = 0  # When the payment has been started.
STATUS_COMPLETED = 1  # When the IPN says its ok.
STATUS_CHECKED = 2  # When someone calls pay-check on the transaction.
# When we we've got a request for a payment, but more work needs to be done
# before we can proceed to the next stage, pending.
STATUS_RECEIVED = 3
# Something went wrong and this transaction failed completely.
STATUS_FAILED = 4
# Explicit cancel action.
STATUS_CANCELLED = 5

STATUS_DEFAULT = STATUS_PENDING

STATUSES = {
    'cancelled': STATUS_CANCELLED,
    'checked': STATUS_CHECKED,
    'completed': STATUS_COMPLETED,
    'failed': STATUS_FAILED,
    'pending': STATUS_PENDING,
    'received': STATUS_RECEIVED,
}

TYPE_PAYMENT = 0
TYPE_REFUND = 1
TYPE_REVERSAL = 2

TYPE_DEFAULT = TYPE_PAYMENT

TYPES = {
    'payment': TYPE_PAYMENT,
    'refund': TYPE_REFUND,
    'reversal': TYPE_REVERSAL
}

SOURCE_PAYPAL = 0
SOURCE_BANGO = 1

SOURCES = {
    'paypal': SOURCE_PAYPAL,
    'bango': SOURCE_BANGO
}


def invert(data):
    return [(v, k) for k, v in data.items()]

STATUSES_CHOICES = invert(STATUSES)
TYPES_CHOICES= invert(TYPES)
SOURCES_CHOICES = invert(SOURCES)
