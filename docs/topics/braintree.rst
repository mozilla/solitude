.. _braintree:

Braintree
#########

Generate a token
----------------

Calls braintree `ClientToken.generate <https://developers.braintreepayments.com/javascript+python/reference/request/client-token/generate>`_:

.. http:post:: /braintree/token/generate/

    **Request**

    No parameters.

    **Response**

    .. code-block:: json

        {
            "token": "<token id>"
        }

    :status 200: token successfully generated.
