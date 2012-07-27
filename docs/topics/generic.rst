.. _generic:

========================
Generic
========================

The generic API points for buyers and sellers.

Buyers
========================

Buyers are identified by a UUID as a string (max 255 chars) that makes sense to
the client. It must be unique within solitude, so we'd recommend prefixing the
UID, eg: `marketplace:....`

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


Sellers
========================

Sellers are identified by a UUID as a string (max 255 chars) that makes sense to
the client. It must be unique within solitude, so we'd recommend prefixing the
UID, eg: `marketplace:....`

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

