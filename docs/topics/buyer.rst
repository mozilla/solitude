.. _buyers:

========================
Buyers API
========================

Buyers are identified by a UUID as a string (max 255 chars) that makes sense to
the client. It must be unique within solitude, so we'd recommend prefixing the
UID, eg: `marketplace:....`

Buyer
=====

Buyers are added to solitude by a POST. The POST should contain a unique UUID
for example::

        POST /generic/buyer/
        {"uuid": "93e33277-87f7-417b-8ed2-371672b5297e"}

You can else get the details of a buyer::

        GET /generic/buyer/64/

Returns::

        {u'paypal': None,
         u'uuid': u'59138729-bcb2-420d-ac25-83f5521d12d4',
         u'resource_uri': u'/generic/buyer/66/'}

PayPal
======

The PayPal table contains the PayPal specific data for that user. Create it by
a POST::

        POST /paypal/buyer/
        {"buyer": "/generic/buyer/64/"}

Now you can check that element individually or the root buyer object.

Because the pre-approval key is sensitive, we'll only return True or False that
it exists, not its contents::

        GET /generic/buyer

Returns::

        {u'paypal':
                {u'buyer': u'/generic/buyer/64/',
                 u'currency': None,
                 u'resource_uri': u'/paypal/buyer/64/',
                 u'key': False,
                 u'expiry': None},
         u'uuid': u'59138729-bcb2-420d-ac25-83f5521d12d4',
         u'resource_uri': u'/generic/buyer/66/'}

Now the `paypal` field of the buyer data is populated with the PayPal data.
