# -*- coding: utf-8 -*-
import functools
import optparse
import uuid

import lib

parser = optparse.OptionParser(usage='%prog [options]')
parser.add_option('--url', default='http://localhost:2602',
                  help='root URL to Solitude. Default: %default')

parser.add_option('--service_id',
                  help='A valid Boku service-id.')
(options, args) = parser.parse_args()


call = functools.partial(lib.call, options.url)

seller_uuid = str(uuid.uuid4())

print 'Creating seller for:', seller_uuid
res = call('/generic/seller/', 'post', {'uuid': seller_uuid})
print res
seller_uri = res['resource_uri']

print 'Retrieving boku sellers.'
res = call('/boku/seller/', 'get', {})

print 'Creating boku seller for:', seller_uri
seller = {
    'seller': seller_uri,
    'service_id': options.service_id,
}
res = call('/boku/seller/', 'post', seller)
boku_seller_id = res['id']

print 'Retrieving the created boku seller'
boku_seller_url = '/boku/seller/{0}/'
res = call(boku_seller_url.format(boku_seller_id), 'get', {})
assert res['service_id'] == options.service_id
assert res['resource_uri'] == boku_seller_url.format(boku_seller_id)

print 'Updating the created seller.'
res = call('/boku/seller/{0}/'.format(boku_seller_id), 'put', seller)

transaction_uuid = str(uuid.uuid4())
user_uuid = str(uuid.uuid4())

print 'Starting a transaction'
transaction = {
    'callback_url': 'http://testing.com/notification',
    'forward_url': 'http://testing.com/result',
    'country': 'MX',
    'transaction_uuid': transaction_uuid,
    'price': '15.00',
    'seller_uuid': seller_uuid,
    'user_uuid': user_uuid,
}
res = call('/boku/transactions/', 'post', transaction)
print 'Transaction started', res
assert 'transaction_id' in res
print 'Buy URL', res['buy_url']
