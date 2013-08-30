.. _generic:

Generic
#######

The generic API can be used for buyers and sellers.

Buyers
======

Buyers are identified by a UUID, which is a string (max 255 chars) that makes
sense to the client. It must be unique within solitude, so we'd recommend
prefixing the UUID, eg: `marketplace:<your-uuid>`

Create
------

Buyers are added to solitude by an HTTP `POST` call. The POST should contain
a unique UUID as well as the PIN the buyer has chosen::

    POST /generic/buyer/
    {"uuid": "93e33277-87f7-417b-8ed2-371672b5297e",
     "pin": "8472"}

Get Details
-----------

You can also get the details of a buyer::

    GET /generic/buyer/64/

Returns:

.. code-block:: javascript

    {"paypal": null,
     "uuid": "93e33277-87f7-417b-8ed2-371672b5297e",
     "resource_uri": "/generic/buyer/66/",
     "pin": true,
     "pin_confirmed": false,
     "new_pin": false,
     "active": true,
     "needs_pin_reset": false,
     "pin_failures": 0,
     "pin_locked_out": false}


Confirm PIN
-----------

Once you have created a buyer with a PIN, you'll need to have the buyer confirm
their PIN. Once you've received their confirmed PIN you can POST to the
``confirm_pin`` endpoint like so::

    POST /generic/confirm_pin/
    {"uuid": "93e33277-87f7-417b-8ed2-371672b5297e",
     "pin": "8472"}

Which will return whether it succeeded or not:

.. code-block:: javascript

    {"confirmed": true}

If there were errors they'll appear like so:

.. code-block:: javascript

    {"confirmed": false,
     "errors": {"uuid": ["Uuid does not exist."]}}


Verify PIN
----------

Once you have a buyer with a confirmed pin, the next time they go to purchase
something you can simply verify their PIN using the ``verify_pin`` endpoint::

    POST /generic/verify_pin/
    {"uuid": "93e33277-87f7-417b-8ed2-371672b5297e",
     "pin": "8472"}

Which has a return value that looks like:

.. code-block:: javascript

    {"valid": true,
     "locked": false}

Errors are handled much in the same way as ``confirm_pin``.

Reset
-----

To start the reset flow, set the ``needs_pin_reset`` attribute on the buyer by
patching the buyer::

    PATCH /generic/buyer/66/
    {"needs_pin_reset": true}

Which returns nothing if it worked. It will 404 if the buyer does not exist.

Next you get the buyer's new pin and patch the buyer again::

    PATCH /generic/buyer/66/
    {"new_pin": "8259"}

Which again returns nothing if it worked and 404 if the buyer does not exist.

After these two steps you will use the ``reset_confirm_pin`` endpoint. It works
the same way as the ``confirm_pin`` endpoint but instead checks against the
buyer's ``new_pin`` rather than their ``pin``::

    POST /generic/reset_confirm_pin/
    {"uuid": "93e33277-87f7-417b-8ed2-371672b5297e",
     "pin": "8259"}

This will return whether it was confirmed:

.. code-block:: javascript

    {"confirmed": true}

If there were errors they'll appear like so:

.. code-block:: javascript

    {"confirmed": false,
     "errors": {"uuid": ["Uuid does not exist."]}}



Sellers
=======

Sellers are identified by a UUID, which is a string (max 255 chars) that makes
sense to the client. It must be unique within solitude, so we'd recommend
prefixing the UUID, eg: `marketplace:<your-uuid>`

Sellers are added to solitude by a `POST` call. The POST should contain a unique UUID::

    POST /generic/seller/
    {"uuid": "acb21517-df02-4734-8173-176ece310bc1"}

You can else get the details of a seller::

    GET /generic/seller/9/

Returns:

.. code-block:: javascript

    {"paypal": null,
     "uuid": "acb21517-df02-4734-8173-176ece310bc1",
     "resource_uri": "/generic/seller/9/"
     "resource_key": 16,
     "bluevia": null,
     "paypal": null}


Transaction
===========

A transaction is created at the start of a payment through solitude. Its
status is altered as the transaction is completed or cancelled as appropriate.

To iterate over the list of transactions::

    GET /generic/transaction/

To get an individual transaction::

    GET /generic/transaction/9/

Example response:

.. code-block:: json

        {
            "amount": "0.62",
            "buyer": null,
            "created": "2013-04-15T05:39:22",
            "currency": "GBP",
            "notes": "",
            "provider": 1,
            "related": null,
            "relations": [],
            "resource_pk": 2977,
            "resource_uri": "/generic/transaction/2977/",
            "seller_product": "/generic/product/449/",
            "status": 5,
            "type": 0,
            "uid_pay": "230450",
            "uid_support": "0",
            "uuid": "webpay:d8d143f3-d484-4903-bd29-bae3d280c5b3"
        }

Statuses:

* 0: ``Pending`` - when the transaction has started, the payment flow has been
  started and has been redirected on to the payment provider. For Bango, this
  is pretty much right away. This is the default.

* 1: ``Completed`` - the payment has been fully completed and processed.

* 2: ``Checked`` - the payment is in process and has been checked. This can be
  checked by a server to server notice (IPN for Paypal, Event Notification
  for Bango) or a manual transaction check. When checking to see if
  a transaction is successful, check to see if its ``Completed`` or
  ``Checked``.

* 3: ``Received`` - we have received the transaction, but have not acted on it
  yet. This is an intermediate step between starting the
  transaction and passing it on to the payment provider. Bango does not use
  this.

* 4: ``Failed`` - an error occurred and the transaction failed.

* 5: ``Cancelled`` - the transaction was cancelled explicitly by the user.
