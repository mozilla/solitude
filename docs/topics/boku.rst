.. _boku:

Boku
#####

For information on how to integrate with Boku see the Boku technical
documentation. Unfortunately this is not public documentation and is available
on the Mozilla mana server, which is only available to Mozilla employees.

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

    :status 200: succesfully processed.
    :status 400: problem with the data.
