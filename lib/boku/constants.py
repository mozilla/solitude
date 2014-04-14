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

COUNTRY_CHOICES = (
    ('MX', 'MX'),
)
