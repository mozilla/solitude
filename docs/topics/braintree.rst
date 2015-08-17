.. _braintree:

Braintree
#########

Make sure your :ref:`braintree-settings` are up to date so that
Solitude can connect to the API.

Tokens
------

Calls braintree `ClientToken.generate <https://developers.braintreepayments.com/javascript+python/reference/request/client-token/generate>`_:

.. http:post:: /braintree/token/generate/

    :>json string token: the token returned by Braintree.
    :status 200: token successfully generated.

Customers
---------

Creates a customer in Braintree and the corresponding buyer and Braintree buyer
in solitude. If the buyer exists in solitude already, it is not created. If the
customer exists in Braintree already, it is not created.

.. http:post:: /braintree/customer/

    :<json string uuid: the uuid of the buyer in solitude.

    .. code-block:: json

        {
            "braintree": {
                "created_at": "2015-05-06T15:35:41.519",
                "id": "customer-id",
                "updated_at": "2015-05-06T15:35:41.519"
            },
            "mozilla": {
                "active": true,
                "braintree_id": "customer-id",
                "buyer": "/generic/buyer/3/",
                "counter": 0,
                "created": "2015-05-06T15:35:41.523",
                "id": 2,
                "modified": "2015-05-06T15:35:41.523",
                "resource_pk": 2,
                "resource_uri": "/braintree/mozilla/buyer/2/"
            }
        }

    :>json string braintree id: id.
    :>json string braintree created_at: created date and time.
    :>json string braintree updated_at: updated date and time.

    :status 201: customer and Braintree buyer successfully created.

.. _braintree-buyer-label:

Data stored in solitude
+++++++++++++++++++++++

Some information is stored in solitude after creating a customer.

.. http:get:: /braintree/mozilla/buyer/<buyer id>/

    :<json string uuid: the uuid of the buyer in solitude.
    :<json string nonce: the payment nonce returned by Braintree.

    .. code-block:: json

        {
            "active": true,
            "braintree_id": "customer-id",
            "buyer": "/generic/buyer/3/",
            "counter": 0,
            "created": "2015-05-06T15:35:41.523",
            "id": 2,
            "modified": "2015-05-06T15:35:41.523",
            "resource_pk": 2,
            "resource_uri": "/braintree/mozilla/buyer/2/"
        }

    :>json boolean active: if the buyer is currently active.
    :>json string braintree_id: the id of the customer on Braintree. This field
                                is read only.
    :>json string buyer: URI to :ref:`a buyer object <buyer-label>`

.. http:patch:: /braintree/mozilla/buyer/<buyer id>/

    :<json boolean active: if the buyer is currently active.

.. http:get:: /braintree/mozilla/buyer/

    :query buyer: the primary key of the buyer.
    :query active: the active status.

.. _payment-methods-label:

Payment Methods
---------------

Create or update a payment method in Braintree and the corresponding payment
method in solitude.

.. http:post:: /braintree/paymethod/

    :<json string buyer_uuid: the uuid of the buyer in solitude.
    :<json string nonce: the payment nonce returned by Braintree.

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

    :>json string braintree token: id of the payment method in Braintree.
    :>json string braintree created_at: created date and time.
    :>json string braintree updated_at: updated date and time.

    :status 201: payment method created.

Delete a payment method. This will delete the payment method in Braintree
and is not reversible.

.. http:post:: /braintree/paymethod/delete/

    :<json string paymethod: the resource_uri of the payment method in solitude.

    :status 204: payment method deleted.

Data stored in solitude
+++++++++++++++++++++++

Some information about the payment method is stored in solitude.

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

.. http:get:: /braintree/mozilla/paymethod/

    :query braintree_buyer: the primary key of the braintree_buyer.
    :query braintree_buyer__buyer__uuid: the uuid for the buyer.
    :query active: the active status.

.. _subscription-label:

Subscriptions
-------------

Create a subscription in Braintree and the corresponding subscription in
solitude.

.. http:post:: /braintree/subscription/

    :<json string paymethod: the uri of the payment method.
    :<json string plan: the id of the plan being purchased.

    .. code-block:: json

        {
            "braintree": {
                "created_at": "2015-05-06T13:34:53.746",
                "id": "some:id",
                "updated_at": "2015-05-06T13:34:53.746"
            },
            "mozilla": {
                "active": true,
                "counter": 0,
                "created": "2015-05-06T13:34:53.763",
                "id": 1,
                "modified": "2015-05-06T13:34:53.763",
                "paymethod": "/braintree/mozilla/paymethod/1/",
                "provider_id": "some:id",
                "resource_pk": 1,
                "resource_uri": "/braintree/mozilla/subscription/1/",
                "seller_product": "/generic/product/1/"
            }
        }

    :>json string braintree id: id of the subscription in braintree.
    :>json string braintree created_at: created date and time.
    :>json string braintree updated_at: updated date and time.

    :status 201: payment method created.

Change payment method on a subscription:

.. http:post:: /braintree/subscription/paymethod/change/

    :<json string paymethod: the resource_uri of the paymethod in solitude.
    :<json string subscription: the resource_uri of the subscription in solitude.

    :status 200: subscription changed.

Cancel a subscription. This will cancel the subscription in Braintree and is
not reversible.

.. http:post:: /braintree/subscription/cancel/

    :<json string subscription: the resource_uri of the subscription in solitude.

    The response is in the same format as for creation.

    :status 200: subscription cancelled.

Data stored in solitude
+++++++++++++++++++++++

Some information about the subscripton is stored in solitude.

.. http:get:: /braintree/mozilla/subscription/<subscription id>/

    .. code-block:: json

        {
            "active": true,
            "counter": 0,
            "created": "2015-05-01T18:21:49",
            "id": 1,
            "paymethod": "/braintree/mozilla/paymethod/2/",
            "modified": "2015-05-01T18:21:49",
            "provider_id": "some:id",
            "resource_pk": 1,
            "resource_uri": "/braintree/mozilla/subscription/1/",
            "seller_product": "/generic/product/2/"
        }

    :>json boolean active: active flag for the method.
    :>json string provider_id: an id for the subscription on the provider,
                               this field is read only.
    :>json string paymethod: the URI to `a payment object <payment-methods-label>`_.
    :>json string seller_product: the URI to `a seller product
                                  <seller-product>`_.

.. http:patch:: /braintree/mozilla/subscription/<subscription id>/

    :<json boolean active: if the subscription is currently active.

.. http:get:: /braintree/mozilla/subscription/

    :query active: if the subscription is active.
    :query paymethod: the primary key of the payment method.
    :query paymethod__braintree_buyer: the primary key of the braintree buyer.
    :query paymethod__braintree_buyer__buyer: the primary key of the buyer.
    :query provider_id: the plan id for this subscription.
    :query seller_product: the primary key of the product.

Sale
----

A sale is a one off payment to call the Braintree Transaction API. For more
information see the `Braintree documentation <https://developers.braintreepayments.com/javascript+python/reference/request/transaction/sale>`_.

This should not be used for subscriptions.

.. http:post:: /braintree/sale/

    :<json amount: the amount of the transaction, within the maximum and minimum limits
    :<json product_id: the product_id as defined by `payments-config <https://github.com/mozilla/payments-config/>`_.
    :<json nonce: (optional) the payment nonce returned by Braintree, used when no payment method is stored.
    :<json paymethod: (optional) the URI to `a payment object <payment-methods-label>`_.

    .. code-block:: json

        {
          "mozilla": {
            "generic": {
              "resource_pk": 1,
              "related": null,
              "seller_product": "/generic/product/1/",
              "currency": "USD",
              "uid_pay": null,
              "uuid": "",
              "uid_support": "test-id",
              "relations": [],
              "seller": "/generic/seller/1/",
              "source": null,
              "provider": 4,
              "pay_url": null,
              "type": 0,
              "status": 2,
              "buyer": null,
              "status_reason": null,
              "created": "2015-08-17T19:17:04.296",
              "notes": null,
              "amount": "5.00",
              "carrier": null,
              "region": null,
              "resource_uri": "/generic/transaction/1/"
            },
            "braintree": {
              "kind": "",
              "transaction": "/generic/transaction/1/",
              "next_billing_period_amount": null,
              "created": "2015-08-17T19:17:04.298",
              "paymethod": null,
              "counter": 0,
              "billing_period_end_date": null,
              "modified": "2015-08-17T19:17:04.298",
              "next_billing_date": null,
              "resource_pk": 1,
              "resource_uri": "/braintree/mozilla/transaction/1/",
              "billing_period_start_date": null,
              "id": 1,
              "subscription": null
            }
          },
          "braintree": {}
        }


    :>json mozilla.generic: the generic transaction object.
    :>json mozilla.generic.buyer: this will be the buyer or empty if no buyer is registered.
    :>json mozilla.braintree: the braintree transaction object.

Notes:
* either a `nonce` or a `paymethod` must exist, but not both

Webhook
-------

When Braintree completes certain actions, they will make a request to the
configured webhook URL. That will be `payments-service <https://github.com/mozilla/payments-service/>`_
which then passes it on to this endpoint. For more information see the
`Braintree documentation <https://developers.braintreepayments.com/javascript+python/reference/general/webhooks>`_.

.. http:get:: /braintree/webhook/

    :query bt_challenge string: the bt_challenge issued by Braintree.
    :>json string: a token returned by the Braintree verify API.

    :status 200: token verified and returned.

.. http:post:: /braintree/webhook/

    :<json bt_signature: the bt_signature issued by Braintree.
    :<json bt_payload: the bt_payload issued by Braintree.

    .. code-block:: json

        {
          "mozilla": {
            "buyer": {
              "active": true,
              "email": "email@example.com",
              "needs_pin_reset": false,
              "new_pin": false,
              "pin": false,
              "pin_confirmed": false,
              "pin_failures": 0,
              "pin_is_locked_out": false,
              "pin_was_locked_out": false,
              "resource_pk": 32,
              "resource_uri": "/generic/buyer/32/",
              "uuid": "dc728c67-bcf8-4237-962d-cb15b2916e21"
            },
            "paymethod": {
              "resource_pk": 22,
              "resource_uri": "/braintree/mozilla/paymethod/22/",
              "braintree_buyer": "/braintree/mozilla/buyer/31/",
              "id": 22,
              "created": "2015-06-16T18:03:43.902",
              "modified": "2015-06-16T18:03:43.902",
              "counter": 0,
              "active": true,
              "provider_id": "29e66c1b-6824-4a41-80d2-fa58ec8fb206",
              "type": 1,
              "type_name": "",
              "truncated_id": ""
            },
            "subscription": {
              "resource_pk": 12,
              "resource_uri": "/braintree/mozilla/subscription/12/",
              "paymethod": "/braintree/mozilla/paymethod/22/",
              "seller_product": "/generic/product/18/",
              "id": 12,
              "created": "2015-06-16T18:03:43.904",
              "modified": "2015-06-16T18:03:43.904",
              "counter": 0,
              "active": true,
              "provider_id": "some-bt:id"
            },
            "transaction": {
              "generic": {
                "amount": "10",
                "buyer": "/generic/buyer/32/",
                "carrier": null,
                "created": "2015-06-16T18:03:43.915",
                "currency": "USD",
                "notes": null,
                "pay_url": null,
                "provider": 4,
                "region": null,
                "related": null,
                "relations": [],
                "resource_pk": 7,
                "resource_uri": "/generic/transaction/7/",
                "seller": "/generic/seller/19/",
                "seller_product": "/generic/product/18/",
                "source": null,
                "status": 2,
                "status_reason": "settled",
                "type": 0,
                "uid_pay": null,
                "uid_support": "bt:id",
                "uuid": "f424e706-9c17-4d6a-9287-e6db28e46ec6"
              },
              "braintree": {
                "resource_pk": 5,
                "resource_uri": "/braintree/mozilla/transaction/5/",
                "paymethod": "/braintree/mozilla/paymethod/22/",
                "subscription": "/braintree/mozilla/subscription/12/",
                "transaction": "/generic/transaction/7/",
                "id": 5,
                "created": "2015-06-16T18:03:43.916",
                "modified": "2015-06-16T18:03:43.916",
                "counter": 0,
                "billing_period_end_date": "2015-07-15T18:03:43.904",
                "billing_period_start_date": "2015-06-16T18:03:43.904",
                "kind": "subscription_charged_successfully",
                "next_billing_date": "2015-07-16T18:03:43.904",
                "next_billing_period_amount": "10"
              }
            },
            "product": {
              "seller": "/generic/seller/19/",
              "access": 1,
              "resource_uri": "/generic/product/18/",
              "resource_pk": 18,
              "secret": null,
              "seller_uuids": {
                "bango": null,
                "reference": null
              },
              "public_id": "brick",
              "external_id": "3089c93d-eb16-4233-83d3-37653369ff8c"
            }
          },
          "braintree": {
            "kind": "subscription_charged_successfully"
          }
        }

    Note: some webhooks (such as `subscription_canceled`) may not contain a
    transaction. If that's the case then the `mozilla.transaction` and
    `mozilla.paymethod` fields will be empty.

    :>json mozilla.buyer: a :ref:`buyer <buyer-label>`.
    :>json mozilla.paymethod: a :ref:`payment method <payment-methods-label>` (optional).
    :>json mozilla.product: a :ref:`product <seller-product>`
    :>json mozilla.subscription: a :ref:`subscription <subscription-label>`.
    :>json mozilla.transaction.generic: a :ref:`generic transaction <transaction-label>` (optional).
    :>json mozilla.transaction.braintree: a :ref:`braintree transaction <braintree-transaction-label>` (optional).
    :>json braintree.kind: the kind of webhook.
    :>json braintree.next_billing_period_amount: the amount of the next charge.
    :>json braintree.next_billing_date: the date of the next charge.
    :status 200: webhook parsed successfully, solitude may have acted on the webhook and
                 is returning data with the expectation that the client will as well.
    :status 204: webhook parsed successfully, however solitude did not act on the
                 webhook and does not expect the caller to act either.

.. _braintree-transaction-label:

Transaction
-----------

The webhook returns transaction details to solitude. Solitude then creates a
generic transaction object. It also creates a Braintree transaction that
contains some information about the purchase transaction.

.. http:get:: /braintree/mozilla/transaction/<transaction id>/

    Get a single braintree transaction object.

    .. code-block:: json

        {
            "id": 1,
            "billing_period_end_date": "2015-07-10T12:20:19.926",
            "billing_period_start_date": "2015-06-11T12:20:19.926",
            "created": "2015-06-11T12:20:19.926",
            "counter": 0,
            "kind": "disbursement",
            "modified": "2015-06-11T12:20:19.926",
            "next_billing_date": "2015-07-11T12:20:19.926",
            "next_billing_period_amount": "10.00",
            "paymethod": "/braintree/mozilla/paymethod/2/",
            "resource_pk": 1,
            "resource_uri": "/generic/transaction/1/",
            "subscription": "/braintree/mozilla/subscription/2/",
            "transaction": "/generic/transaction/2/"
        }

    :>json string paymethod: the URI to `a payment object <payment-methods-label>`_.
    :>json string subscription: the URI to `a subscription object <subscription-label:l>`_.
    :>json string transaction: the URI to `a transaction object <_transaction-label>`_.

    The fields `kind`, `next_billing_date`, `next_billing_period_amount`,
    `billing_period_end_date`, `billing_period_start_date` are copies of the data
    from Braintree. Please see the Braintree documentation for more information.

.. http:get:: /braintree/mozilla/transaction/

    Get all braintree transactions.

    :query transaction__buyer__uuid:
        only get transactions belonging to this
        :ref:`generic buyer <buyer-label>` UUID.

Development Tips
----------------

When developing on systems that rely on Braintree data in Solitude
you can reset some data with the ``./manage.py braintree_reset`` script.
See the ``--help`` output for details.
