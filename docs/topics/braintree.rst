.. _braintree:

Braintree
#########

Generate a token
----------------

Calls braintree `ClientToken.generate <https://developers.braintreepayments.com/javascript+python/reference/request/client-token/generate>`_:

.. http:post:: /braintree/token/generate/

    :>json string token: the token returned by Braintree.
    :status 200: token successfully generated.

Create a customer
-----------------

Creates a customer in Braintree and the corresponding buyer in solitude. If the
buyer exists in solitude already, it is not created. If the customer exists in
Braintree already, it is not created.

.. http:post:: /braintree/customer/

    :<json string uuid: the uuid of the buyer in solitude.

    Returns :ref:`a buyer object <buyer-label>` with some extra fields.

    .. code-block:: json

        {
            "active": true,
            "braintree": {
                "created_at": "2015-04-27T21:35:51",
                "id": "123",
                "updated_at": "2015-04-27T21:35:51"
            },
            "email": null,
            "needs_pin_reset": false,
            "new_pin": false,
            "pin": false,
            "pin_confirmed": false,
            "pin_failures": 0,
            "pin_is_locked_out": false,
            "pin_was_locked_out": false,
            "resource_pk": 8,
            "resource_uri": "/generic/buyer/8/",
            "uuid": "123"
        }

    :>json string braintree id: id.
    :>json string braintree created_at: created date and time.
    :>json string braintree updated_at: updated date and time.

    :status 200: customer and buyer already exist.
    :status 201: customer or buyer successfully created.
