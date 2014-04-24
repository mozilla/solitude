# -*- coding: utf-8 -*-
import functools
import optparse
import urllib
import uuid

import lib

parser = optparse.OptionParser(usage='%prog [options]')
parser.add_option('--url', default='http://localhost:8001',
                  help='root URL to Solitude. Default: %default')

parser.add_option('--service_id',
                  help='A valid Boku service-id.')
(options, args) = parser.parse_args()


call = functools.partial(lib.call, options.url)


def create_generic_seller(seller_uuid):
    print 'Creating a generic seller:', seller_uuid
    res = call('/generic/seller/', 'post', {'uuid': seller_uuid})
    print res
    return res['resource_uri']


# Create a Product Seller
# This should probably be removed becuase we have
# separate sellers for each provider, so single seller
# for a shared product doesn't make sense.
product_seller_uuid = str(uuid.uuid4())
product_seller_uri = create_generic_seller(product_seller_uuid)

# Create a shared product
print 'Creating a generic seller product.'
external_id = str(uuid.uuid4())
public_id = str(uuid.uuid4())
res = call('/generic/product/', 'post', {
    'seller': product_seller_uri,
    'external_id': external_id,
    'secret': 'n',
    'public_id': public_id,
    'access': 1,
})
seller_product_uri = res['resource_uri']


# Bango Testing
bango_seller_uuid = str(uuid.uuid4())
bango_seller_uri = create_generic_seller(bango_seller_uuid)

print 'Create bango package.'
res = call('/bango/package/', 'post', {
    'seller': bango_seller_uri,
    'adminEmailAddress': 'admin@place.com',
    'supportEmailAddress': 'support@place.com',
    'financeEmailAddress': 'finance@place.com',
    'paypalEmailAddress': 'paypal@place.com',
    'vendorName': u'འབྲུག་ཡུལ།',
    'companyName': 'Some Company, LLC',
    'address1': '111 Somewhere',
    'addressCity': 'Pleasantville',
    'addressState': 'CA',
    'addressZipCode': '11111',
    'addressPhone': '4445551111',
    'countryIso': 'USA',
    'currencyIso': 'USD'
})
seller_bango_uri = res['resource_uri']
package_id = res['package_id']

print 'Retrieving login infos.'
res = call('/bango/login/', 'post', {
    'packageId': str(package_id),
})

bango_url = 'http://mozilla.com.test.bango.org/login/al.aspx?{params}'.format(
    params=urllib.urlencode({
        'packageId': package_id,
        'personId': res['person_id'],
        'emailAddress': res['email_address'],
        'authenticationToken': res['authentication_token'],
    })
)
print 'You should be logged in against: ' + bango_url

print 'Getting SBI agreement'
res = call('/bango/sbi/agreement/', 'get', {
    'seller_bango': seller_bango_uri,
})

print 'Agreeing to SBI agreement'
res = call('/bango/sbi/', 'post', {
    'seller_bango': seller_bango_uri,
})

print 'Making product and updating rating.'
res = call('/provider/bango/product/', 'post', {
    'seller_bango': seller_bango_uri,
    'seller_product': seller_product_uri,
    'name': 'A product name',
    'packageId': package_id,
    'categoryId': 1,
    'secret': 'A secret',
})
bango_product_uri = res['resource_uri']

print 'Create bank details.'
res = call('/bango/bank/', 'post', {
    'seller_bango': seller_bango_uri,
    'bankAccountPayeeName': 'Andy',
    'bankAccountNumber': 'Yes',
    'bankAccountCode': '123',
    'bankName': 'Bailouts r us',
    'bankAddress1': '123 Yonge St',
    'bankAddressZipCode': 'V1V 1V1',
    'bankAddressIso': 'BRA'
})

print 'Checking bango id, as an example.'
res = call(bango_product_uri, 'get', {})

res = call(seller_bango_uri, 'get', {})
old_support_id = res['support_person_id']
old_financial_id = res['finance_person_id']

# print 'Update addresses.'
# res = call(seller_bango_uri, 'patch', {
#     'supportEmailAddress': 'foo@foo.com',
#     'financeEmailAddress': 'foo@foo.com',
# })

res = call(seller_bango_uri, 'get', {})
print res
print ('Support id %s to %s' % (old_support_id, res['support_person_id']))
print ('Finance id %s to %s' % (old_financial_id, res['finance_person_id']))

print 'Request billing configuration.'
call('/bango/billing/', 'post', {
    'pageTitle': 'yep',
    'prices': [{'price': 1, 'currency': 'USD', 'method': 1}],
    'transaction_uuid': str(uuid.uuid4()),
    'user_uuid': str(uuid.uuid4()),
    'seller_product_bango': bango_product_uri,
    'redirect_url_onerror': 'https://marketplace-dev.allizom.org/mozpay/err',
    'redirect_url_onsuccess': 'https://marketplace-dev.allizom.org/mozpay/ok',
})

# Boku Testing
boku_seller_uuid = str(uuid.uuid4())
print 'Creating a boku seller for:', boku_seller_uuid
boku_seller_uri = create_generic_seller(boku_seller_uuid)

print 'Creating boku seller for:', boku_seller_uri
res = call('/boku/seller/', 'post', {
    'seller': boku_seller_uri,
    'service_id': options.service_id,
})

boku_seller_id = res['id']
boku_seller_uri = res['resource_uri']

print 'Creating boku product for:', boku_seller_uri
res = call('/boku/product/', 'post', {
    'seller_boku': boku_seller_uri,
    'seller_product': seller_product_uri,
})

print 'Starting a boku transaction'
transaction_uuid = str(uuid.uuid4())
user_uuid = str(uuid.uuid4())

transaction = {
    'callback_url': 'http://testing.com/callback/',
    'forward_url': 'http://testing.com/forward/',
    'country': 'MX',
    'transaction_uuid': transaction_uuid,
    'price': '15.00',
    'seller_uuid': boku_seller_uuid,
    'user_uuid': user_uuid,
}
res = call('/boku/transactions/', 'post', transaction)
print 'Transaction started', res
assert 'transaction_id' in res
assert 'buy_url' in res


# Retrieve the generic product and check its supported sellers
res = call(
    '/generic/product/?public_id={public_id}'.format(public_id=public_id),
    'get',
    {}
)
assert res['meta']['total_count'] == 1
product_data = res['objects'][0]
assert product_data['seller_uuids']['bango'] == bango_seller_uuid
assert product_data['seller_uuids']['boku'] == boku_seller_uuid
print 'Generic product correctly configured for multiple payment accounts'
