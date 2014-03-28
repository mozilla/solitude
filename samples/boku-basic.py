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
merchant_id = '12345'
service_id = '12345'
call = functools.partial(lib.call, options.url)

print 'Retrieving sellers.'
res = call('/boku/sellers/', 'get', {})

print 'Creating seller for:', uid
seller = {
    'uuid': uid,
    'status': 'ACTIVE',
    'merchant_id': merchant_id,
    'service_id': service_id,
}
res = call('/boku/sellers/', 'post', seller)
seller_id = res['id']

print 'Retrieving the created seller'
seller_url = '/boku/sellers/{0}/'
res = call(seller_url.format(seller_id), 'get', {})
assert res['merchant_id'] == merchant_id
assert res['service_id'] == service_id
assert res['resource_uri'] == seller_url.format(seller_id)

print 'Updating the created seller.'
seller['merchant_id'] = '54321'
res = call('/boku/sellers/{0}/'.format(seller_id), 'put', seller)
assert res['name'] == '54321'

product_uuid = options.product_uuid or str(uuid.uuid4())
external_id = options.product_external_id or str(uuid.uuid4())

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
res = call('/boku/transactions/', 'post', transaction)
assert res['status'] == 'STARTED'
