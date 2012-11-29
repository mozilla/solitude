STATUS_PENDING = 0
STATUS_COMPLETED = 1  # When the IPN says its ok.
STATUS_CHECKED = 2  # When someone calls pay-check on the transaction.

STATUS_DEFAULT = STATUS_PENDING

STATUSES = {
    'pending': STATUS_PENDING,
    'completed': STATUS_COMPLETED,
    'checked': STATUS_CHECKED,
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
