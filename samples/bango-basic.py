# -*- coding: utf-8 -*-
import json
import pprint
import sys
import urllib
import uuid

import requests

try:
    # Read the root from the command line, rather than hard coding.
    root = sys.argv[1]
except:
    root = 'http://localhost:8001'


def call(url, method, data):
    method = getattr(requests, method)
    url = root + url
    print 'Calling url:', url
    print 'Request data:'
    pprint.pprint(data)
    data = json.dumps(data)
    result = method(url, data=data,
                    headers={'content-type': 'application/json'})
    print 'Status code:', result.status_code
    if result.status_code not in (200, 201, 202, 204):
        print 'Error:', result.content
        sys.exit()

    if result.content:
        print 'Response data:'
        data = result.json
        pprint.pprint(data)
        print
        return data

    print


uid = str(uuid.uuid4())

print 'Creating for:', uid
print 'Creating seller.'
res = call('/generic/seller/', 'post', {'uuid': uid})
print res
seller_uri = res['resource_uri']

print 'Creating seller product.'
external_id = str(uuid.uuid4())
res = call('/generic/product/', 'post', {'seller': seller_uri,
                                         'external_id': external_id,
                                         'secret': 'n',
                                         'public_id': uid,
                                         'access': 1})
seller_product_uri = res['resource_uri']

print 'Create bango package.'
res = call('/bango/package/', 'post', {
    'seller': seller_uri,
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

bango_url = ('http://mozilla.com.test.bango.org/login/al.aspx?%s' %
    urllib.urlencode({
        'packageId': package_id,
        'personId': res['person_id'],
        'emailAddress': res['email_address'],
        'authenticationToken': res['authentication_token'],
    }))
print 'You should be logged in against: ' + bango_url

print 'Getting SBI agreement'
res = call('/bango/sbi/agreement/', 'get', {
    'seller_bango': seller_bango_uri,
})

print 'Agreeing to SBI agreement'
res = call('/bango/sbi/', 'post', {
    'seller_bango': seller_bango_uri,
})

print 'Creating seller bango product.'
res = call('/bango/product/', 'post', {
    'seller_bango': seller_bango_uri,
    'seller_product': seller_product_uri,
    'name': 'A name for the number',
    'categoryId': 1,
    'packageId': 1,
    'secret': 'n'
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

print 'Making premium.'
res = call('/bango/premium/', 'post', {
    'bango': '123',
    'price': 1,
    'currencyIso': 'EUR',
    'seller_product_bango': bango_product_uri
})

print 'Updating rating.'
res = call('/bango/rating/', 'post', {
    'bango': '123',
    'rating': 'UNIVERSAL',
    'ratingScheme': 'GLOBAL',
    'seller_product_bango': bango_product_uri
})

print 'Updating rating.'
res = call('/bango/rating/', 'post', {
    'bango': '123',
    'rating': 'GENERAL',
    'ratingScheme': 'USA',
    'seller_product_bango': bango_product_uri
})



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
