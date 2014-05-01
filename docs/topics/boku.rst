.. _boku:

Boku
#####

For information on how to integrate with Boku see the Boku technical
documentation. Unfortunately this is not public documentation and is available
on the Mozilla mana server, which is only available to Mozilla employees.

Verify Service ID
=================

Verify that a Service ID is valid for use with Boku in Solitude.

.. http:post:: /boku/verify_service/

    **Request**

    service_id - The Boku service ID.

    .. code-block:: json

        {
            "service_id": "<service id>"
        }

    **Response**

    :status 204: successfully verified the service id.
    :status 400: unable to verify the service id.

Start Transaction
=================

Start a transaction with Boku.

.. http:post:: /boku/start_transaction/

    **Request**

    :param callback_url: A URL that Boku notifies when the transaction is
                         complete.
    :param forward_url: A URL that Boku redirects the client to
                        after successful/failed payment.
    :param country: The `ISO 3166-1-alpha-2`_ country code of the purchaser.
    :param transaction_uuid: A unique identifier to track the transaction.
    :param price: The purchase price in Decimal format (2 decimal places).
                  It must match one of the existing price points in Boku.
    :param seller_uuid: The UUID of the seller as it is stored in Solitude.
    :param user_uuid: A unique identifier for the purchaser.

    .. code-block:: json

        {
            "callback_url": "http://webpay.com/boku/pay/notification",
            "forward_url": "http://webpay.com/boku/pay/finished",
            "country": "CA",
            "transaction_uuid": "<transaction uuid>",
            "price": "15.00",
            "seller_uuid": "<seller uuid>",
            "user_uuid": "<user uuid>"
        }

    **Response**

    .. code-block:: json

        {
            "transaction_id": "<transaction id>",
            "buy_url": "http://example.com/123/buy.js"
        }

    :status 200: successfully processed.
    :status 400: problem with the data.

.. _`ISO 3166-1-alpha-2`: http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2

Event
=====

Processes a server to server event sent from Boku to Webpay. As specified in
the `billingresult` callback notification. This API overrides the underlying
provider call.

.. http:post:: /provider/boku/event/

    **Request**

    This example shows the required parameters. Boku sends a large number of
    parameters, as per the docs. All other parameters are ignored.

    This will update the transaction in solitude and set it to completed,
    filling out any missing data.

    .. code-block:: json

        {
            "trx-id": "some:trxid",
            "param": "some:uuid",
            "currency": "USD",
            "amount": "0.99",
            "sig": "some:sig",
            "action": "billingresult"
        }

    **Response**

    :status 200: successfully processed.
    :status 400: problem with the data.
