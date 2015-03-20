============
Proxy
============

To add a further layer of security, Solitude can be run in two modes:

* *standalone*: in this case Solitude is only run with **one instance** and
  communicates to the payment providers (PayPal, Bango etc). That one instance
  knows everything about how to interact with the database and has the
  appropriate settings for communicating with those providers.

  * Requests go: **client** > **solitude** > **provider**.


* *proxy*: in this case Solitude is run with **two instances**, a database
  server and proxy server.

  * Requests go: **client** > **solitude database server** > **solitude proxy server** > **provider**.

  * *database server* this **can** read and write to the database, the cache and
    so on. It **cannot** talk to the provider. It has no provider credentials.

  * *proxy server* this **cannot** read and write to the database, the cache
    and so on. It **can** talk to provider. It has the provider credentials.

By default solitude runs in standalone mode. Running using `runserver` or the
`wsgi/playdoh.py` script will run in this mode.

Running both the database and proxy server on the same instance might not give
you much of an advantage. The intention is to run them in seperate servers and
have appropriate security between them.

To run in proxy mode, make the following changes:

* *database server* ensure you have not specified any sensitive provider
  settings.

  * For Bango set `BANGO_PROXY` to point to the *proxy server* referencing
    the path `/proxy/bango` for example::

        BANGO_PROXY = 'https://some.server.local/proxy/bango'

  * For payment providers using *zippy*, set `ZIPPY_PROXY` to point to the
    *proxy server* referencing the path `/proxy/provider` for example::

        BANGO_PROXY = 'https://some.server.local/proxy/provider'

    You should also ensure that you do not have the *auth* section in your
    `ZIPPY_CONFIGURATION` dictionary, since the *database server* will not be
    referencing the *auth*.

* *proxy server* ensure you have not specified any database or cache settings,
  but have specified the provider settings, such as username, password, sandbox
  and so on.

  * For zippy, ensure that the `ZIPPY_CONFIGURATION` configuration has the
    *auth* dictionary and *url* string.

To run the proxy server, run with the environment variable::

    SOLITUDE_PROXY='enabled'

To run as a wsgi file, just use `wsgi/proxy.py` and it will set this variable
for you.

Errors
======

If the proxy encounters a response code that is not a 2xx code then it will
log a warning that there might be issues for the db instance. Example::

    s.proxy:ERROR Warning response status: 404

In this case it's up to the client to deal with the issue before continuing
processing. It might be acceptable for the API to return a 404 or 302 and the
client knows how to deal with that.

If the client has a fatal error::

    s.proxy:ERROR ConnectionError: [Errno 8] nodename nor servname provided, or not known

This will return a response of 500 to the calling library. It's that libraries
job to cope with the 500 errors. In this case the Bango client in solitude
detects 500 and raises a `ProxyError`::

    File "/Users/andy/sandboxes/solitude/lib/bango/client.py\", line 133, in send
        raise ProxyError(msg)
            "type": "<class 'lib.bango.errors.ProxyError'>",
            "value": "Proxy returned: 500 from: https://webservices.test.bango.org/mozillaexporter/service.asmx"

Testing
=======

When solitude with proxy is setup, run a test command against the service.

For Bango, from the command line, with all the solitude requirements
installed::

    cd samples
    python bango-basic.py

If you've got an error talking to Bango you'll get a proxy error as outlined
above.
