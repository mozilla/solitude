.. _bango:

===================
Bango
===================

Sellers
===================

The Bango tables contains the Bango specific data for that seller. First you'll
need to create a Bango package by a POST::

        POST /bango/package/
        {"seller": "/generic/seller/9",
         ...}

Package
=======

TODO: insert more notes about packages.

A GET on a package will query the local solitude database about that package::

        GET /bango/package/9/

Returns::

        {"full": {},
         "created": "2013-01-30T09:41:34",
         "support_person_id": 232941,
         ...}

The *full* field represents data polled from Bango. To get that information,
send through *full* in the GET body. For example::

        GET /bango/package/9/
        {"full": true}

Returns::


        {"full": {
          "vatNumber": null,
          "supportEmailAddress": "support@example.com",
          ...}
         "created": "2013-01-30T09:41:34",
         "support_person_id": 232941,
         ...}

SBI Agreement
=============

The SBI Agreement is 3 API calls (GetSBIAgreement, GetAcceptedSBIAgreement and
AcceptSBIAgreement) rolled into one. You will need a valid Bango Seller in
solitude to call this API::

        GET /bango/sbi/agreement/
        {"seller_bango": "/bango/package/29/"}

This will return the text of the agreement and when the agreement will be valid
for.

To set the agreement as approved::

        POST /bango/sbi/
        {"seller_bango": "/bango/package/29/"}

This will return when the agreement was accepted and when it's valid too. The
expiry date is also stored on the seller, so you can access that as well::

        GET /bango/package/29/
        {"sbi_expires": "2014-01-23"}

If *sbi_expires* is empty, the agreement has not been approved.

Refunds
=======

The refund API gives access to 2 calls: DoRefund and GetRefundStatus. You will
need a valid transaction to start a refund::

        POST /bango/refund/
        {"uuid": "uuid-of-the-transaction"}

This will return the bango response and a pointer to the **new transaction**.
A refund generates a new transaction::

        GET /bango/refund/status/
        {"uuid": "uuid-of-the-refund-transaction"}

If the response from Bango is different from the transaction state, then the
transaction will be altered to reflect this.
