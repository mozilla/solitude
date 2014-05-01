from lib.transactions import constants as trans_const

CURRENCIES = {
    'MXN': 'Mexican Pesos',
}

# Boku transaction API returns values with no decimal places.
# So 100 is really Decimal('1.00'). Some API's tell you the number of decimal
# places, some do not. This lookup is used to figure out what value to use.
#
# Take the amount from Boku and divide by this number.
DECIMAL_PLACES = {
    'MXN': 100,
}

# Boku country choices as specified in ISO 3166-1-alpha-2.
COUNTRY_CHOICES = (
    ('MX', 'MX'),
)

# This is a map of error codes returned from the Boku verify API that
# can be translated into transaction statuses.
# These error codes are the same as the "testing codes" on Mana:
# https://mana.mozilla.org/wiki/display/MARKET/Boku
TRANS_STATUS_FROM_VERIFY_CODE = {
    4: trans_const.STATUS_FAILED,
    5: trans_const.STATUS_FAILED,
    7: trans_const.STATUS_FAILED,
    8: trans_const.STATUS_CANCELLED,
    11: trans_const.STATUS_FAILED,
}
