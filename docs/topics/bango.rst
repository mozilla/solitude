.. _bango:

Bango
#####

For more information on the specific Bango APIs see: https://wiki.mozilla.org/Marketplace/BangoPayments

Sellers
=======

The Bango tables contains the Bango specific data for that seller. First you'll
need to create a Bango "package" by doing a POST call:

.. http:post:: /bango/package/

    Example successful seller creation:

    .. code-block:: json

        {
            "seller": "/generic/seller/9",
            ...
        }


Packages
========

A `GET` on a package will query the local solitude database about that package:

.. http:get:: /bango/package/9/

    **Response**

    Example successful seller creation:

    .. code-block:: json

        {
            "full": {},
            "created": "2013-01-30T09:41:34",
            "support_person_id": 232941,
        }

The `full` field represents data polled from Bango. To get that information,
send through `full` in the GET body. For example:

.. http:get:: /bango/package/9/

    **Request**

    Example:

    .. code-block:: json

        {
            "full": true
        }

    **Response**

    Example successful seller creation:

    .. code-block:: json

        {
            "full": {
                "vatNumber": null,
                "supportEmailAddress": "support@example.com",
                ...
            },
            "created": "2013-01-30T09:41:34",
            "support_person_id": 232941,
            ...
        }


SBI Agreement
=============

The SBI Agreement is 3 API calls (GetSBIAgreement, GetAcceptedSBIAgreement and
AcceptSBIAgreement) rolled into one. You will need a valid Bango Seller in
solitude to call this API:

.. http:get:: /bango/sbi/agreement/

    **Response**

    Example successful SBI retrieval:

    .. code-block:: json

        {
            "seller_bango": "/bango/package/29/"
        }

This will return the text of the agreement and when the agreement will be valid
for.

To set the agreement as approved:

.. http:post:: /bango/sbi/

    **Response**

    Example successful SBI approved:

    .. code-block:: json

        {
            "seller_bango": "/bango/package/29/"
        }

This will return when the agreement was accepted and when it's valid too. The
expiry date is also stored on the seller, so you can access that as well:

.. http:get:: /bango/package/29/

    **Response**

    Example successful SBI retrieval:

    .. code-block:: json

        {
            "sbi_expires": "2014-01-23"
        }


If *sbi_expires* is empty, the agreement has not been approved.

Refunds
=======

The refund API gives access to two Bango calls: "DoRefund" and
"GetRefundStatus". You will need a valid payment transaction to start a refund.

.. http:post:: /bango/refund/

    Refund a payment.

    **Request**

    :param uuid: id of the payment transaction.

    Example:

    .. code-block:: json

        {
            "uuid": "uuid-of-the-payment-transaction"
        }

    **Response**

    :status 201: refund processed. Examine the response contents to see the
        status of the refund and a pointer to the new refund.
    :status 400: there was a problem with the transaction chosen. Examine the
        response contents for more information.
    :status 404: transaction not found at all.

    :param uuid: the uuid of the transaction.
    :param status: the Bango response.
    :param transaction: the URL of the newly created transaction.

    Example successful refund:

    .. code-block:: json

        {
            "fake_response": null,
            "resource_pk": 2,
            "resource_uri": "/bango/refund/2/",
            "status": "OK",
            "transaction": "/generic/transaction/2/",
            "uuid": "sample:uid"
        }

.. http:get:: /bango/refund/status/

    Look up the status of refund.

    .. note:: If the response from Bango is different from the transaction
        state, then the transaction is updated to reflect the refund's new
        status. This might happen for PENDING refunds.

    **Request**

    :param uuid: uuid of the refund transaction.

    Example:

    .. code-block:: json

        {
            "uuid": "sample:uid"
        }

    **Response**

    :status 200: successfully completed.

    :param status: the Bango response.
    :param transaction: the URL of the refund transaction.

    .. code-block:: json

        {
            "fake_response": null,
            "resource_pk": 1,
            "resource_uri": "/bango/refund/1/",
            "status": "OK",
            "transaction": "/generic/transaction/1/"
        }
