.. _auth.rst:

Authentication
##############

Most API requests can enforce zero-legged OAuth by having a shared key and
secret on the servers. This allows solitude to check the client sending
requests is allowed to do so. By default, this is `True`::

    REQUIRE_OAUTH = True
    CLIENT_OAUTH_KEYS = {
        'marketplace': 'please change this',
        'webpay': 'please change this',
    }

In development, you might want to connect with curl and other tools. For that
alter the `REQUIRE_OAUTH` setting to `False`.

.. note::

    Service URLs do not require JWT encoding.
