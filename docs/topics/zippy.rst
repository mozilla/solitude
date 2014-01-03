Zippy
#####

Documentation on zippy and reference implementation.

Note that in the following examples ``{*uuid}`` refers to an actual ``uuid``.

Sellers
=======

.. http:post:: /provider/reference/sellers/

    Create a seller.

    **Request**

    :param uuid: uuid of the seller.
    :param email: email of the seller.
    :param name: name of the seller.
    :param status: status of the seller.

    Example:

    .. code-block:: json

        {
            "email": "jdoe@example.org",
            "name": "John",
            "status": "ACTIVE",
            "uuid": "{seller-uuid}"
        }

    **Response**

    :status 201: seller created. Examine the response contents to see the
        status of the seller and a pointer to the new seller.
    :status 400: there was a problem with the seller creation. Examine the
        response contents for more information.

    :param uuid: the uuid of the seller.
    :param email: email of the seller.
    :param name: name of the seller.
    :param status: status of the seller.
    :param agreement: an optional date that can be used for terms validation.
    :param resource_name: the name of the resource.
    :param resource_pk: the primary key of the resource.
    :param resource_uri: the URI of the resource.

    Example successful seller creation:

    .. code-block:: json

        {
            "agreement": "",
            "email": "jdoe@example.org",
            "name": "John",
            "resource_name": "sellers",
            "resource_pk": "{seller-uuid}",
            "resource_uri": "/sellers/{seller-uuid}",
            "status": "ACTIVE",
            "uuid": "{seller-uuid}"
        }


.. http:get:: /provider/reference/sellers/{seller-uuid}/

    Retrieve a seller.

    **Response**

    :status 200: seller retrieved. Examine the response contents to see the
        status of the seller and a pointer to the seller.
    :status 400: there was a problem with the seller retrieval. Examine the
        response contents for more information.

    :param uuid: the uuid of the seller.
    :param email: email of the seller.
    :param name: name of the seller.
    :param status: status of the seller.
    :param agreement: an optional date that can be used for terms validation.
    :param resource_name: the name of the resource.
    :param resource_pk: the primary key of the resource.
    :param resource_uri: the URI of the resource.

    Example successful seller retrieval:

    .. code-block:: json

        {
            "agreement": "",
            "email": "jdoe@example.org",
            "name": "John",
            "resource_name": "sellers",
            "resource_pk": "{seller-uuid}",
            "resource_uri": "/sellers/{seller-uuid}",
            "status": "ACTIVE",
            "uuid": "{seller-uuid}"
        }


.. http:put:: /provider/reference/sellers/{seller-uuid}/

    Update a seller.

    **Request**

    All parameters are optionals.

    :param uuid: uuid of the seller.
    :param email: email of the seller.
    :param name: name of the seller.
    :param status: status of the seller.

    Example:

    .. code-block:: json

        {
            "name": "Jack"
        }

    **Response**

    :status 201: seller created. Examine the response contents to see the
        status of the seller and a pointer to the seller.
    :status 400: there was a problem with the seller modification. Examine the
        response contents for more information.

    :param uuid: the uuid of the seller.
    :param email: email of the seller.
    :param name: name of the seller.
    :param status: status of the seller.
    :param agreement: an optional date that can be used for terms validation.
    :param resource_name: the name of the resource.
    :param resource_pk: the primary key of the resource.
    :param resource_uri: the URI of the resource.

    Example successful seller modification:

    .. code-block:: json

        {
            "agreement": "",
            "email": "jdoe@example.org",
            "name": "Jack",
            "resource_name": "sellers",
            "resource_pk": "{seller-uuid}",
            "resource_uri": "/sellers/{seller-uuid}",
            "status": "ACTIVE",
            "uuid": "{seller-uuid}"
        }


Products
========

Using that newly created "seller", we can now create a "product".

.. http:post:: /provider/reference/products/

    Create a product.

    **Request**

    :param seller_id: uuid of the seller.
    :param external_id: uuid of the product.
    :param name: name of the product.

    Example:

    .. code-block:: json

        {
            "name": "Product name",
            "seller_id": "{seller-uuid}",
            "external_id": "{product-uuid}"
        }

    **Response**

    :status 201: product created. Examine the response contents to see the
        status of the product and a pointer to the new product.
    :status 400: there was a problem with the product creation. Examine the
        response contents for more information.

    :param seller_id: uuid of the seller.
    :param external_id: uuid of the product.
    :param name: name of the product.
    :param status: status of the product.
    :param resource_name: the name of the resource.
    :param resource_pk: the primary key of the resource.
    :param resource_uri: the URI of the resource.

    Example successful product creation:

    .. code-block:: json

        {
            "external_id": "{product-uuid}",
            "seller_id": "{seller-uuid}",
            "name": "Product name",
            "resource_name": "products",
            "resource_pk": "{product-uuid}",
            "resource_uri": "/products/{product-uuid}",
            "status": "ACTIVE"
        }


Transactions
============

Let's buy that product by creating a "transaction".

.. http:post:: /provider/reference/transactions/

    Create a transaction.

    **Request**

    :param carrier: the carrier of the transaction.
    :param currency: the currency of the transaction.
    :param price: the price of the transaction.
    :param product_id: uuid of the product.
    :param ext_transaction_id: uuid of the transaction.
    :param pay_method: the payment method of the transaction.
    :param region: the region concerned by the transaction.
    :param error_url: the URL to reach in case of error of the transaction.
    :param success_url: the URL to reach in case of success of the transaction.

    Example:

    .. code-block:: json

        {
            "carrier": "USA_TMOBILE",
            "currency": "EUR",
            "price": "0.99",
            "product_id": "{product-uuid}",
            "error_url": "http://marketplace.firefox.com/mozpay/provider/error/",
            "success_url": "http://marketplace.firefox.com/mozpay/provider/success/",
            "ext_transaction_id": "{transaction-uuid}",
            "pay_method": "OPERATOR",
            "region": "123"
        }

    **Response**

    :status 201: transaction created. Examine the response contents to see the
        status of the transaction and the token.
    :status 400: there was a problem with the transaction creation. Examine the
        response contents for more information.

    :param carrier: the carrier of the transaction.
    :param currency: the currency of the transaction.
    :param price: the price of the transaction.
    :param product_id: uuid of the product.
    :param ext_transaction_id: uuid of the transaction.
    :param pay_method: the payment method of the transaction.
    :param region: the region concerned by the transaction.
    :param error_url: the URL to reach in case of error of the transaction.
    :param success_url: the URL to reach in case of success of the transaction.
    :param resource_name: the name of the resource.
    :param resource_pk: the primary key of the resource.
    :param resource_uri: the URI of the resource.
    :param status: status of the transaction. Should be STARTED at this point.
    :param token: the security token for the transaction.

    Example successful transaction creation:

    .. code-block:: json

        {
            "carrier": "USA_TMOBILE",
            "currency": "EUR",
            "product_id": "{product-uuid}",
            "error_url": "http://marketplace.firefox.com/mozpay/provider/error/",
            "success_url": "http://marketplace.firefox.com/mozpay/provider/success/",
            "ext_transaction_id": "{transaction-uuid}",
            "pay_method": "OPERATOR",
            "price": "0.99",
            "region": "123"
            "resource_name": "transactions",
            "resource_pk": "{product-uuid}",
            "resource_uri": "/transactions/{product-uuid}",
            "token": "97ccb8ced0318a2751e936e354848...",
            "status": "STARTED"
        }


Terms Agreement
===============

.. http:get:: /provider/reference/sellers/{seller-uuid}/

    Retrieve terms related to a given seller.

    **Response**

    :status 200: terms retrieved. Examine the response contents to see the
        content of the terms and an agreement date.
    :status 400: there was a problem with the terms retrieval. Examine the
        response contents for more information.

    :param terms: the text containing terms, can be lengthy.
    :param agreement: the datetime of the agreement of the terms by the user.

    Example successful terms retrieval:

    .. code-block:: json

        {
            "terms": "Terms for seller: John...",
            "agreement": "2013-11-19T11:48:49.158Z"
        }

