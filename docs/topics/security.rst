.. _security:

Security
########

Encryption
==========

Currently we use `django-aesfield <https://github.com/andymckay/django-aesfield>`_
to provide encryption on key fields. We'd recommend more levels of database
encryption or file system encryption.

The encryption uses AES to do this.

Encrypted fields:

* buyers email
* sellers secret
* bango signature

The keys per field are mapped in settings. See :ref:`setup.rst` for more.

Hashed fields
=============

Fields are

* buyers pin
* buyers new pin

Requests
========

All requests use OAuth 1.1 which signs the header using a secret key. Requests
must be signed with that key or be rejected.
