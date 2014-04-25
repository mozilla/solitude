.. _auth.rst:

Authentication
##############

Most API requests can enforce zero-legged OAuth by having a shared key and
secret on the servers. This allows solitude to check the client sending
requests is allowed to do so. By default, this is `False`.

To enable `REQUIRE_OAUTH` to `True` and enter the keys that are required,
for example::

    REQUIRE_OAUTH = True
    CLIENT_OAUTH_KEYS = {'webpay': 'some-big-secret'}

.. note::

    Service URLs do not require JWT encoding.
