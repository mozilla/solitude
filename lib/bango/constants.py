import re

ACCESS_DENIED = 'ACCESS_DENIED'
BANGO_ALREADY_PREMIUM_ENABLED = 'BANGO_ALREADY_PREMIUM_ENABLED'
BANK_DETAILS_EXIST = 'BANK_DETAILS_EXIST'
INTERNAL_ERROR = 'INTERNAL_ERROR'
# There is one of these for every field.
INVALID = re.compile('^INVALID_\w+$')
NO_BANGO_EXISTS = 'NO_BANGO_EXISTS'
OK = 'OK'
REQUIRED_CONFIGURATION_MISSING = 'REQUIRED_CONFIGURATION_MISSING'
SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'

HEADERS_SERVICE = 'x-solitude-service'
HEADERS_SERVICE_GET = 'HTTP_X_SOLITUDE_SERVICE'

CURRENCIES = {
    'AUD': 'Australian Dollars',
    'CAD': 'Canadian Dollars',
    'CHF': 'Swiss Francs',
    'DKK': 'Danish Krone',
    'EUR': 'Euro',
    'GBP': 'Pounds Sterling',
    'MYR': 'Malaysian Ringgit',
    'NOK': 'Norwegian Krone',
    'NZD': 'New Zealand Dollars',
    'SEK': 'Swedish Krone',
    'SDG': 'Singapore Dollar',
    'THB': 'Thai Baht',
    'USD': 'US Dollars',
    'ZAR': 'South African Rand',
}

# TODO: Expand this bug 814492.
CATEGORIES = {
    1: 'Games'
}

# List of valid country codes: http://en.wikipedia.org/wiki/ISO_3166-1_alpha-3
COUNTRIES = [
    'BRA',
    'ESP'
]

RATINGS = ['GLOBAL', 'UNIVERSAL', 'RESTRICTED']
RATINGS_SCHEME = ['GLOBAL', 'USA']

PAYMENT_TYPES = ('OPERATOR', 'PSMS', 'CARD', 'INTERNET')


def match(status, constant):
    # There's going to be an INVALID_ something for every field in every form
    # adding them all to this is boring. Let's make a regex to map them.
    if isinstance(constant, basestring):
        return status, constant
    return constant.match(status)
