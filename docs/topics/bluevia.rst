.. _bluevia:

===================
BlueVia
===================

Pay
===================

TODO

Sellers
========================

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
