# -*- coding: utf-8 -*-
import sys
import uuid

from curling.lib import API

ZIPPY_CONFIGURATION = {
    'reference': {
        'url': 'http://127.0.0.1:8080',  # No trailing slash.
        'auth': {
            'key': 'dpf43f3p2l4k3l03',
            'secret': 'kd94hf93k423kf44',
        },
    },
}

try:
    # Read the root from the command line, rather than hard coding.
    root = sys.argv[1]
except:
    root = ZIPPY_CONFIGURATION['reference']['url']


class Client(object):

    def __init__(self, reference_name):
        self.config = ZIPPY_CONFIGURATION.get(reference_name)
        self.api = None
        if self.config:
            self.api = API(self.config['url'], append_slash=False)
            self.api.activate_oauth(self.config['auth']['key'],
                                    self.config['auth']['secret'])


uid = str(uuid.uuid4())

client = Client('reference')
print 'Retrieving sellers.'
res = client.api.sellers.get()
print res
assert res == []

print 'Creating for:', uid
seller = {
    'uuid': uid,
    'status': 'ACTIVE',
    'name': 'John',
    'email': 'jdoe@example.org',
}
res = client.api.sellers.post(seller)
print res
seller_id = res['resource_pk']

print 'Retrieving sellers.'
res = client.api.sellers.get()
print res
assert len(res) == 1

print 'Retrieving the created seller.'
res = client.api.sellers(uid).get()
print res
assert res['name'] == 'John'

print 'Updating the created seller.'
res = client.api.sellers(uid).put({'name': 'Jack'})
print res
assert res['name'] == 'Jack'

external_id = str(uuid.uuid4())
print 'Creating seller product with external_id: ' + external_id
product = {
    'name': 'Product name',
    'seller_id': seller_id,
    'external_id': external_id,
}
res = client.api.products.post(product)
print res
assert res['name'] == 'Product name'

product_id = res['resource_pk']
print 'Creating product transaction with product_id: ' + product_id
transaction = {
    'product_id': product_id,
    'region': '123',
    'carrier': 'USA_TMOBILE',
    'price': '0.99',
    'currency': 'EUR',
    'pay_method': 'OPERATOR'
}
res = client.api.transactions.post(transaction)
print res
assert res['status'] == 'STARTED'

print 'Deleting the created seller.'
res = client.api.sellers(uid).delete()
print res
assert res

print 'Retrieving sellers.'
res = client.api.sellers.get()
print res
assert res == []
