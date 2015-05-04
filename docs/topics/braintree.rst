.. _braintree:

Braintree
#########

Make sure your :ref:`braintree-settings` are up to date so that
Solitude can connect to the API.

Generate a token
----------------

Calls braintree `ClientToken.generate <https://developers.braintreepayments.com/javascript+python/reference/request/client-token/generate>`_:

.. http:post:: /braintree/token/generate/

    :>json string token: the token returned by Braintree.
    :status 200: token successfully generated.

Create a customer
-----------------

Creates a customer in Braintree and the corresponding buyer and Braintree buyer
in solitude. If the buyer exists in solitude already, it is not created. If the
customer exists in Braintree already, it is not created.

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

    :status 200: customer, Braintree buyer and buyer already exist.
    :status 201: customer, Braintree buyer or buyer successfully created.

.. note:: If the creation fails at Braintree then the new buyer objects will
          not be created.

Braintree Buyer
---------------

Stores information about the Buyer in Braintree in solitude. It links a Buyer
object and Braintree customer.

.. note:: Because creation of Braintree buyer is tied to creating a Customer
          in Braintree, creation of a Braintree buyer is not allowed through
          a POST. You must use the "Create a Customer" API.

.. http:get:: /braintree/buyer/<buyer id>/

    .. code-block:: json

        {
            "active": true,
            "braintree_id": "7",
            "buyer": "/braintree/buyer/7/",
            "counter": 0,
            "created": "2015-04-30T11:42:09",
            "modified": "2015-04-30T11:42:09",
            "resource_pk": 1,
            "resource_uri": "/braintree/buyer/1/"
        }

    :>json boolean active: if the buyer is currently active.
    :>json string braintree_id: the id of the customer on Braintree. This field
                                is read only.
    :>json string buyer: URI to :ref:`a buyer object <buyer-label>`

.. http:patch:: /braintree/buyer/<buyer id>/

    :<json boolean active: if the buyer is currently active.

.. http:get:: /braintree/buyer/

    :query buyer: the primary key of the buyer.
    :query active: the active status.
