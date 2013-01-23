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
