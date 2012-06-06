PAYPAL_PERSONAL = {
    'first_name': 'http://axschema.org/namePerson/first',
    'last_name': 'http://axschema.org/namePerson/last',
    'email': 'http://axschema.org/contact/email',
    'full_name': 'http://schema.openid.net/contact/fullname',
    'company': 'http://openid.net/schema/company/name',
    'country': 'http://axschema.org/contact/country/home',
    'payerID': 'https://www.paypal.com/webapps/auth/schema/payerID',
    'post_code': 'http://axschema.org/contact/postalCode/home',
    'address_one': 'http://schema.openid.net/contact/street1',
    'address_two': 'http://schema.openid.net/contact/street2',
    'city': 'http://axschema.org/contact/city/home',
    'state': 'http://axschema.org/contact/state/home',
    'phone': 'http://axschema.org/contact/phone/default'
}
PAYPAL_PERSONAL_LOOKUP = dict([(v, k) for k, v
                                      in PAYPAL_PERSONAL.iteritems()])

PAYPAL_CURRENCIES = {
    'AUD': _('Australian Dollar'),
    'BRL': _('Brazilian Real'),
    'CAD': _('Canadian Dollar'),
    'CZK': _('Czech Koruna'),
    'DKK': _('Danish Krone'),
    'EUR': _('Euro'),
    'HKD': _('Hong Kong Dollar'),
    'HUF': _('Hungarian Forint'),
    'ILS': _('Israeli New Sheqel'),
    'JPY': _('Japanese Yen'),
    'MYR': _('Malaysian Ringgit'),
    'MXN': _('Mexican Peso'),
    'NOK': _('Norwegian Krone'),
    'NZD': _('New Zealand Dollar'),
    'PHP': _('Philippine Peso'),
    'PLN': _('Polish Zloty'),
    'GBP': _('Pound Sterling'),
    'SGD': _('Singapore Dollar'),
    'SEK': _('Swedish Krona'),
    'CHF': _('Swiss Franc'),
    'TWD': _('Taiwan New Dollar'),
    'THB': _('Thai Baht'),
    'USD': _('U.S. Dollar'),
}

OTHER_CURRENCIES = PAYPAL_CURRENCIES.copy()
del OTHER_CURRENCIES['USD']

CURRENCY_DEFAULT = 'USD'
