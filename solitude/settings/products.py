# A definiton of Products for Payments for Firefox Accounts. Marketplace
# defines these dynamically. However for the moment we will define these from
# configuration files.
from decimal import Decimal

products = {
    'concrete': {
        'seller': 'mozilla-concrete',
        'products': [
            {
                'name': 'brick',
                'amount': Decimal('10')
            },
            {
                'name': 'mortar',
                'amount': Decimal('5')
            }
        ]
    }
}
