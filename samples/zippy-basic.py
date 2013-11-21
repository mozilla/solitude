# -*- coding: utf-8 -*-
import functools
import sys
import uuid

import lib

try:
    # Read the root from the command line, rather than hard coding.
    root = sys.argv[1]
except:
    root = 'http://localhost:8001'


uid = str(uuid.uuid4())
call = functools.partial(lib.call, root)

print 'Retrieving sellers.'
res = call('/provider/reference/sellers/', 'get', {})

print 'Creating for:', uid
seller = {
    'uuid': uid,
    'status': 'ACTIVE',
    'name': 'John',
    'email': 'jdoe@example.org',
}
res = call('/provider/reference/sellers/', 'post', seller)
seller_id = res['resource_pk']
seller_uuid = res['uuid']

print 'Retrieving the created seller'
res = call('/provider/reference/sellers/{0}/'.format(seller_uuid), 'get', {})
assert res['name'] == 'John'

print 'Retrieving seller terms.'
res = call('/provider/reference/terms/{0}/'.format(seller_uuid), 'get', {})
assert res['terms'] == 'Terms for seller: John'

print 'Updating the created seller.'
res = call('/provider/reference/sellers/{0}/'.format(seller_uuid), 'put',
           {'name': 'Jack'})
assert res['name'] == 'Jack'

external_id = str(uuid.uuid4())
print 'Creating seller product with external_id: ' + external_id
product = {
    'name': 'Product name',
    'seller_id': seller_id,
    'external_id': external_id,
}
res = call('/provider/reference/products/', 'post', product)
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
res = call('/provider/reference/transactions/', 'post', transaction)
assert res['status'] == 'STARTED'
