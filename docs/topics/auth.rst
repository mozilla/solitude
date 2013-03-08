.. _auth.rst:

Authentication
##############

Most API requests can enforce data to be sent to as JSON Web Tokens (JWT).

This allows solitude to check the client sending requests is allowed to
do so. 

To require JWT authentication, in the settings set `REQUIRE_JWT` to `True`.
Then enter the keys that are required, for example::

    REQUIRE_JWT = True
    CLIENT_JWT_KEYS = {'foo': 'some big secret'}

To use JWT authentication, send a request with the `application/jwt`
Content-Type.

The JWT should contain the key used to encode the JSON in the field
**jwt-encode-key**. The server will look inside the JWT, find the key and
then use it to verify the rest of the contents.

For example, before encoding it could be the following:

.. code-block:: javascript

    {"jwt-encode-key": "foo", "pin: "1234"}

If something happens while decoding the JWT, a reason will be given in the response.
For example::

    curl -H  "Content-Type: application/json" -XPATCH http://localhost:8000/generic/buyer/1/
    {"reason": "JWT is required"}

.. note::

    Service URLs do not require JWT encoding.
