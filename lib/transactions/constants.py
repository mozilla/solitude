from solitude.base import invert

# Please see docs for an explanation of these.
STATUS_PENDING = 0
STATUS_COMPLETED = 1
STATUS_CHECKED = 2
STATUS_RECEIVED = 3
STATUS_FAILED = 4
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
STATUSES_INVERTED = dict((v, k) for k, v in STATUSES.items())


TYPE_PAYMENT = 0
TYPE_REFUND = 1
TYPE_REVERSAL = 2

TYPE_DEFAULT = TYPE_PAYMENT

TYPES = {
    'payment': TYPE_PAYMENT,
    'refund': TYPE_REFUND,
    'reversal': TYPE_REVERSAL
}

PROVIDER_PAYPAL = 0
PROVIDER_BANGO = 1

PROVIDERS = {
    'paypal': PROVIDER_PAYPAL,
    'bango': PROVIDER_BANGO
}

LOG_STATS = 0
LOG_REVENUE = 1

LOGS = {
    'stats': LOG_STATS,
    'revenue': LOG_REVENUE
}

STATUSES_CHOICES = invert(STATUSES)
TYPES_CHOICES = invert(TYPES)
LOG_CHOICES = invert(LOGS)
PROVIDERS_CHOICES = invert(PROVIDERS)
