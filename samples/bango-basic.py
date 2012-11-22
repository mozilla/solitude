import json
import pprint
import sys
import uuid

import requests

root = 'http://localhost:8001'

def call(url, method, data):
    method = getattr(requests, method)
    url = root + url
    print 'Calling url:', url
    print 'Data:'
    pprint.pprint(data)
    data = json.dumps(data)
    result = method(url, data=data,
                    headers={'content-type': 'application/json'})
    print 'Status code:', result.status_code
    if result.status_code not in (200, 201, 202, 204):
        print 'Error:', result.content
        sys.exit()
    print 'Data:'
    pprint.pprint(result.json)
    print
    return result.json

uid = str(uuid.uuid4())

print 'Creating for:', uid
print 'Creating seller.'
res = call('/generic/seller/', 'post', {'uuid': uid})
print res
seller_uri = res['resource_uri']

print 'Creating seller product.'
res = call('/generic/product/', 'post', {'seller': seller_uri, 'secret': 'n'})
seller_product_uri = res['resource_uri']

print 'Create bango package.'
res = call('/bango/package/', 'post', {
    'seller': seller_uri,
    'adminEmailAddress': 'admin@place.com',
    'supportEmailAddress': 'support@place.com',
    'financeEmailAddress': 'finance@place.com',
    'paypalEmailAddress': 'paypal@place.com',
    'vendorName': 'Some Company',
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

print 'Creating seller bango product.'
res = call('/bango/product/', 'post', {
    'seller_bango': seller_bango_uri,
    'seller_product': seller_product_uri,
    'name': 'A name for the number',
    'categoryId': 1,
    'secret': 'n'
})
bango_product_uri = res['resource_uri']

print 'Checking bango id, as an example.'
res = call(bango_product_uri, 'get', {})

print 'Making premium.'
res = call('/bango/make-premium/', 'post',  {
    'bango': '123',
    'price': 1,
    'currencyIso': 'CAD',
    'seller_product_bango': bango_product_uri
})

res = call(seller_bango_uri, 'get', {})
old_support_id = res['support_person_id']
old_financial_id = res['finance_person_id']

print 'Update addresses.'
res = call(seller_bango_uri, 'patch', {
    'supportEmailAddress': 'foo@foo.com',
    'financeEmailAddress': 'foo@foo.com',
})

res = call(seller_bango_uri, 'get', {})
print res
print ('Support id %s to %s' % (old_support_id, res['support_person_id']))
print ('Finance id %s to %s' % (old_financial_id, res['finance_person_id']))
