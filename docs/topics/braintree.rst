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

.. _braintree-buyer-label:

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

Create a payment method
-----------------------

Creates a payment method in Braintree and the corresponding payment method in
solitude.

.. http:post:: /braintree/paymethod/

    :<json string uuid: the uuid of the buyer in solitude.
    :<json string nonce: the payment nonce returned by Braintree.

    Returns :ref:`a payment method object <payment-methods>` with some extra
    fields.

    .. code-block:: json

        {
            "braintree": {
                "created_at": "2015-05-05T14:22:26.650",
                "token": "da-token",
                "updated_at": "2015-05-05T14:22:26.650"
            },
            "mozilla": {
                "active": true,
                "braintree_buyer": "/braintree/mozilla/buyer/16/",
                "counter": 0,
                "created": "2015-05-05T14:22:26.656",
                "id": 4,
                "modified": "2015-05-05T14:22:26.656",
                "provider_id": "da-token",
                "resource_pk": 4,
                "resource_uri": "/braintree/mozilla/paymethod/4/",
                "truncated_id": "7890",
                "type": 1,
                "type_name": "visa"
            }
        }

    :>json string braintree token: id of the payment method in braintree.
    :>json string braintree created_at: created date and time.
    :>json string braintree updated_at: updated date and time.

    :status 201: payment method created.

Data stored in solitude
-----------------------

Information about the payment method is stored in solitude.

.. http:get:: /braintree/mozilla/paymethod/<method id>/

    .. code-block:: json

        {
          "active": true,
          "braintree_buyer": "/braintree/mozilla/buyer/2/",
          "counter": 0,
          "created": "2015-05-05T14:25:38",
          "id": 1,
          "modified": "2015-05-05T14:25:38",
          "provider_id": "da-token",
          "resource_pk": 1,
          "resource_uri": "/braintree/mozilla/paymethod/1/",
          "truncated_id": "some",
          "type": 1,
          "type_name": "visa"
        }

    :>json boolean active: active flag for the method.
    :>json string braintree_buyer: URI to :ref:`a braintree buyer object <braintree-buyer-label>`.
    :>json string provider_id: an id for the payment method on the provider, this field is read only.
    :>json string truncated_id: a truncated id of the payment type, for example
                                for a credit card, the last 4 digits, this field is read only.
    :>json int type: `1` for credit card is currently the only one supported, this field is read only.
    :>json string type_name: name of the type of purchase, this field is read only.

.. http:patch:: /braintree/mozilla/<method id>/

    :<json boolean active: if the buyer is currently active.

.. http:get:: /braintree/mozilla/

    :query braintree_buyer: the primary key of the braintree_buyer.
    :query braintree_buyer__buyer__uuid: the uuid for the buyer.
    :query active: the active status.
