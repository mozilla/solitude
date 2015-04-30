# From zamboni, the different payment types that zamboni knows about.
PAYMENT_METHOD_OPERATOR = 0
PAYMENT_METHOD_CARD = 1
PAYMENT_METHOD_ALL = 2

PAYMENT_METHOD_CHOICES = (
    PAYMENT_METHOD_OPERATOR,
    PAYMENT_METHOD_CARD,
    PAYMENT_METHOD_ALL
)

# Not including "all" which is really "both" because for Payment Methods that
# doesn't make sense.
SINGLE_PAYMENT_METHOD = (
    (PAYMENT_METHOD_OPERATOR, PAYMENT_METHOD_OPERATOR),
    (PAYMENT_METHOD_OPERATOR, PAYMENT_METHOD_CARD)
)
