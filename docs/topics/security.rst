.. _security:

========================
Security
========================

Encryption
========================

Currently we use `django-aesfield <https://github.com/andymckay/django-aesfield>`_
to provide encryption on key fields. We'd recommend more levels of database
encryption or file system encryption.

The encryption uses AES to do this.

Encrypted fields:

* buyer

  * paypal pre-approval key

* seller

  * generic secret

  * paypal paypal_id

  * paypal permissions token

  * paypal permissions secret

  * bluevia bluevia_id

The keys per field are mapped in settings. See :ref:`setup.rst` for more.

Hashed fields
=============

TODO: add notes on this.

Requests
========

All requests use OAuth 1.1 which signs the header using a secret key. Requests
must be signed with that key or be rejected.

*TODO*: Wraithan to add notes here.
