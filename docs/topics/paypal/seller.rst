.. _sellers:

========================
Sellers API
========================

Sellers are identified by a UUID as a string (max 255 chars) that makes sense to
the client. It must be unique within solitude, so we'd recommend prefixing the
UID, eg: `marketplace:....`

Seller
======

Sellers are added to solitude by a POST. The POST should contain a unique UUID
for example::

        POST /generic/seller/
        {"uuid": "acb21517-df02-4734-8173-176ece310bc1"}

You can else get the details of a seller:

        GET /generic/seller/9/

Returns::

        {u'paypal': None,
         u'uuid': u'acb21517-df02-4734-8173-176ece310bc1',
         u'resource_uri': u'/generic/seller/9/'
         u'resource_key': 16,
         u'bluevia': null,
         u'paypal': null}

PayPal
======

The PayPal table contains the PayPal specific data for that seller. Create it by
a POST::

        POST /paypal/seller/
        {"seller": "/generic/seller/9/",
         "paypal_id": "foo@bar.com"}

Now you can check that element individually or the root seller object.

Because the pre-approval key is sensitive, we'll only return True or False that
it exists, not its contents::

        GET /generic/seller/9/

Returns::

        {u'paypal': {
                u'secret': False,
                u'seller': u'/generic/seller/9/',
                u'paypal_id': u'foo@bar.com',
                u'token': False,
                u'resource_uri': u'/paypal/seller/10/'},
         u'uuid': u'acb21517-df02-4734-8173-176ece310bc1',
         u'resource_uri': u'/generic/seller/9/'}

Now the `paypal` field of the seller data is populated with the PayPal data.

The PayPal seller data supports a PUT for updates.

BlueVia Support
====================

To create a bluevia id::

        POST /bluevia/seller/
        {"bluevia_id": "some:id",
         "seller": "/generic/seller/9/"}

Returns::

        {"resource_pk": 1,
         "seller": "/generic/seller/9/",
         "bluevia_id": "some:id",
         "resource_uri": "/bluevia/seller/1/"}

You can do PUT and PATCH on the bluevia seller to alter the id.
