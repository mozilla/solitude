# -*- coding: utf-8 -*-
import functools
import optparse
import uuid

import lib

parser = optparse.OptionParser(usage='%prog [options]')
parser.add_option('--url', default='http://localhost:2602',
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


seller_uid = options.seller_uuid or 'seller:' + str(uuid.uuid4())
call = functools.partial(lib.call, options.url)

##################################################################
# First set up the sellers and products.
#
print 'Creating generic seller.'
res = call('/generic/seller/', 'post', {'uuid': seller_uid})
seller_uri = res['resource_uri']

print 'Creating generic product.'
external_id = 'external:' + str(uuid.uuid4())
product_id = 'product:' + str(uuid.uuid4())
res = call('/generic/product/', 'post', {'seller': seller_uri,
                                         'external_id': external_id,
                                         'secret': 'n',
                                         'public_id': product_id,
                                         'access': 1})
seller_product_uri = res['resource_uri']

print 'Create reference seller for:', seller_uid
seller = {
    'seller': seller_uri,
    'uuid': seller_uid,
    'name': 'John',
    'email': 'jdoe@example.org',
    'status': 'ACTIVE',
}
res = call('/provider/reference/sellers/', 'post', seller)
reference_uri = res['resource_uri']
seller_id = res['id']

print 'Get reference seller for:', seller_uid
res = call(reference_uri, 'get', {})

print 'Creating reference product for:', seller_uid
product = {
    'seller_product': seller_product_uri,
    'seller_reference': reference_uri,
    'name': 'example-product',
    'uuid': 'reference-uuid:' + product_id
}

res = call('/provider/reference/products/', 'post', product)
reference_product_uri = res['resource_uri']

print 'Checking we can find the reference product for:', seller_uid
res = call(reference_product_uri, 'get', {})
print res

print 'Getting reference product for:', seller_uid
res = call(reference_product_uri, 'get', {})

print 'Retrieving seller terms.'
res = call('/provider/reference/terms/{0}/'.format(seller_id), 'get', {})
assert res['reference']['text'] == 'Terms for seller: John'

print 'Updating the created seller.'
seller['name'] = 'Jack'
seller['agreement'] = '2010-01-01'
res = call('/provider/reference/sellers/{0}/'.format(seller_id), 'put', seller)
assert res['reference']['name'] == 'Jack'

print 'Get reference seller for:', seller_uid
res = call(reference_uri, 'get', {})

print 'Checking that given a public id, we can get the reference seller.'
res = call('/generic/product/?public_id={0}'.format(product_id), 'get', {})
assert res['objects'][0]['seller_uuids']['reference'], seller_uid

external_id = options.product_external_id or str(uuid.uuid4())

print 'Creating product transaction with product_id: ' + product_id
base_url = 'http://marketplace.firefox.com/mozpay'
transaction = {
    'product_id': 'reference-uuid:' + product_id,
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
