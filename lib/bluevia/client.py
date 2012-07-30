import calendar
import time

import jwt


class Client(object):

    def create_jwt(self, id='', secret='', **data):
        assert id and secret, 'Id and secret required'
        issued_at = calendar.timegm(time.gmtime())
        purchase = {
            'aud': data['aud'],
            'exp': issued_at + 3600,
            # Expires in 1 hour, should this be configurable?
            'iat': issued_at,
            'iss': id,
            'request': {
                'name': data['app_name'],
                'description': data['app_description'],
                'price': str(data['amount']),
                'currencyCode': data['currency'],
                'postbackURL': data['postback_url'],
                'chargebackURL': data['chargeback_url'],
                'productData': data['product_data']
            },
            'typ': 'tu.com/payments/inapp/v1',
        }
        return jwt.encode(purchase, secret)


def get_client():
    return Client()
