# -*- coding: utf-8 -*-
import functools
import optparse
import uuid

import lib

parser = optparse.OptionParser(usage='%prog [options]')
parser.add_option('--url', default='http://localhost:8001',
                  help='root URL to Solitude. Default: %default')
parser.add_option('--seller-uuid',
                  help='Create seller with this UUID. If not '
                       'specified, one will be generated.')
parser.add_option('--product-uuid',
                  help='Create a product with this UUID. If not '
                       'specified, one will be generated.')
parser.add_option('--product-external-id',
                  help='Create a product with this external ID. If not '
                       'specified, one will be generated.')
(options, args) = parser.parse_args()


uid = options.seller_uuid or str(uuid.uuid4())
call = functools.partial(lib.call, options.url)

print 'Retrieving sellers.'
res = call('/provider/reference/sellers/', 'get', {})

print 'Creating seller for:', uid
seller = {
    'uuid': uid,
    'status': 'ACTIVE',
    'name': 'John',
    'email': 'jdoe@example.org',
}
res = call('/provider/reference/sellers/', 'post', seller)
seller_id = res['id']

print 'Retrieving the created seller'
seller_url = '/provider/reference/sellers/{0}/'
res = call(seller_url.format(seller_id), 'get', {})
assert res['name'] == 'John'
assert res['resource_uri'] == seller_url.format(seller_id)

print 'Retrieving seller terms.'
res = call('/provider/reference/terms/{0}/'.format(seller_id), 'get', {})
assert res['text'] == 'Terms for seller: John'

print 'Updating the created seller.'
seller['name'] = 'Jack'
res = call('/provider/reference/sellers/{0}/'.format(seller_id), 'put', seller)
assert res['name'] == 'Jack'

product_uuid = options.product_uuid or str(uuid.uuid4())
external_id = options.product_external_id or str(uuid.uuid4())

print 'Creating seller product with external_id: ' + external_id
product = {
    'name': 'Product name',
    'seller_id': seller_id,
    'external_id': external_id,
    'uuid': product_uuid,
}
res = call('/provider/reference/products/', 'post', product)
assert res['name'] == 'Product name'

product_id = res['id']
print 'Creating product transaction with product_id: ' + product_id
base_url = 'http://marketplace.firefox.com/mozpay'
transaction = {
    'product_id': product_id,
    'region': '123',
    'carrier': 'USA_TMOBILE',
    'price': '0.99',
    'currency': 'EUR',
    'pay_method': 'OPERATOR',
    'callback_success_url': base_url + '/callback/sucess/',
    'callback_error_url': base_url + '/callback/error/',
    'success_url': base_url + '/provider/sucess/',
    'error_url': base_url + '/provider/error/',
    'ext_transaction_id': str(uuid.uuid4())
}
res = call('/provider/reference/transactions/', 'post', transaction)
assert res['status'] == 'STARTED'
