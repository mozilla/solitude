.. _auth.rst:

========================
Authentication
========================

Most API requests can enforce data to be sent to as JWT. This allows solitude
to do a limited level of authentication that the client sending requests is
allowed to do so. To require JWT authentication, in settings set::

        REQUIRE_JWT = False

Then enter the keys that are required, for example::

        CLIENT_JWT_KEYS = {'foo': 'some big secret'}

To use JWT authentication send a request with the content type::

        application/jwt

The JWT should contain the key used to encode the JSON in the field
**jwt-encode-key**. The server will look inside the JWT, find the key and
then use that to verify the rest of the contents.

For example before encoding, it could like this::

        {"jwt-encode-key": "foo", "pin: "1234"}

If there any errors decoding the JWT, there will be a reason in the response.
For example::

        curl -H  "Content-Type: application/json"
             -XPATCH http://localhost:8000/generic/buyer/1/
        {"reason": "JWT is required"}

**Note**: service URLs do not require JWT encoding.
