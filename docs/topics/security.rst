.. _security:

========================
Security
========================

Encryption
========================

Currently we use `django-mysql-aesfield <https://github.com/andymckay/django-mysql-aesfield>`_
to provide encryption on key fields. We'd recommend more levels of database
encryption or file system encryption.

The encryption uses MySQL AES to do this.

Encrypted fields:

* buyer

  * paypal pre-approval key

* seller

  * paypal paypal_id

  * paypal permissions token

  * paypal permissions secret

The keys per field are mapped in settings. See :ref:`setup` for more.

Requests
========

All requests use OAuth 1.1 which signs the header using a secret key. Requests
must be signed with that key or be rejected.

*TODO*: Wraithan to add notes here.
