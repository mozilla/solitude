.. _services.rst:

Services
########

These are resources to provide information to clients about the status.

.. http:get:: /services/request/

    Echoes information back about the requet.

    **Response**

    :param authenticated: the OAuth key used to authenticate.
    :status 200: successful.

.. http:get:: /services/status/

    Returns information about things solitude needs. Useful for nagios.

    **Response**

    Example:

    .. code-block:: json

        {
            "meta":
            {
                "limit": 20,
                "next": null,
                "offset": 0,
                "previous": null,
                "total_count": 1
            },
            "objects":
            [{
                "cache": true,
                "db": true,
                "resource_uri": "",
                "settings": true
            }]
        }

    :status 200: successful.
    :status 500: theres a problem on the server.
