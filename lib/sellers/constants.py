from solitude.base import invert


EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE = 'EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE'

ACCESS_PURCHASE = 1
ACCESS_SIMULATE = 2

ACCESS_TYPES = {
    # The product can be purchased.
    'purchase': ACCESS_PURCHASE,
    # The product can only go through a simulated purchase.
    'simulate': ACCESS_SIMULATE,
}

ACCESS_CHOICES = invert(ACCESS_TYPES)
