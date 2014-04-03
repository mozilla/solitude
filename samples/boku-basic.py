# -*- coding: utf-8 -*-
import functools
import optparse
import uuid

import lib

parser = optparse.OptionParser(usage='%prog [options]')
parser.add_option('--url', default='http://localhost:8001',
                  help='root URL to Solitude. Default: %default')
(options, args) = parser.parse_args()


call = functools.partial(lib.call, options.url)

seller_uuid = str(uuid.uuid4())
merchant_id = '12345'
service_id = '12345'

print 'Creating seller for:', seller_uuid
res = call('/generic/seller/', 'post', {'uuid': seller_uuid})
print res
seller_uri = res['resource_uri']

print 'Retrieving boku sellers.'
res = call('/boku/seller/', 'get', {})

print 'Creating boku seller for:', seller_uri
seller = {
    'seller': seller_uri,
    'merchant_id': merchant_id,
    'service_id': service_id,
}
res = call('/boku/seller/', 'post', seller)
boku_seller_id = res['id']

print 'Retrieving the created boku seller'
boku_seller_url = '/boku/seller/{0}/'
res = call(boku_seller_url.format(boku_seller_id), 'get', {})
assert res['merchant_id'] == merchant_id
assert res['service_id'] == service_id
assert res['resource_uri'] == boku_seller_url.format(boku_seller_id)

print 'Updating the created seller.'
seller['merchant_id'] = '54321'
res = call('/boku/seller/{0}/'.format(boku_seller_id), 'put', seller)
assert res['merchant_id'] == '54321'

product_uuid = options.product_uuid or str(uuid.uuid4())
external_id = options.product_external_id or str(uuid.uuid4())

product_id = '123' 
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
