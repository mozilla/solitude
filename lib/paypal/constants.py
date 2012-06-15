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
    'AUD': 'Australian Dollar',
    'BRL': 'Brazilian Real',
    'CAD': 'Canadian Dollar',
    'CZK': 'Czech Koruna',
    'DKK': 'Danish Krone',
    'EUR': 'Euro',
    'HKD': 'Hong Kong Dollar',
    'HUF': 'Hungarian Forint',
    'ILS': 'Israeli New Sheqel',
    'JPY': 'Japanese Yen',
    'MYR': 'Malaysian Ringgit',
    'MXN': 'Mexican Peso',
    'NOK': 'Norwegian Krone',
    'NZD': 'New Zealand Dollar',
    'PHP': 'Philippine Peso',
    'PLN': 'Polish Zloty',
    'GBP': 'Pound Sterling',
    'SGD': 'Singapore Dollar',
    'SEK': 'Swedish Krona',
    'CHF': 'Swiss Franc',
    'TWD': 'Taiwan New Dollar',
    'THB': 'Thai Baht',
    'USD': 'U.S. Dollar',
}

OTHER_CURRENCIES = PAYPAL_CURRENCIES.copy()
del OTHER_CURRENCIES['USD']

CURRENCY_DEFAULT = 'USD'

REFUND_OK_STATUSES = ['REFUNDED', 'REFUNDED_PENDING',
                      'ALREADY_REVERSED_OR_REFUNDED']

IPN_STATUS_OK = 'OK'
IPN_STATUS_IGNORED = 'IGNORED'
IPN_STATUS_ERROR = 'ERROR'

IPN_ACTION_REFUND = 'REFUND'
IPN_ACTION_PAYMENT = 'PAYMENT'
IPN_ACTION_REVERSAL = 'REVERSAL'
