.. _setup.rst:

Setup
#####

This is a standard Django or Playdoh project so the setup should be pretty
straight forward. Requirements:

* MySQL
* Python 2.7

For more information see the playdoh_ installation docs.

Requirements
------------

If you don't have Python or MySQL installed. On OS X, homebrew_ is
recommended::

    brew install python mysql

Don't forget to set the default mysql password for your `root` user
in that case (an empty password is possible)::

    mysql -uroot -p

Optionally install a virtualenv_.

Install
-------

From github::

    git clone git://github.com/mozilla/solitude.git

If you used a virtualenv_ activate it and compile some playdoh dependencies::

    cd solitude
    pip install --no-deps -r requirements/dev.txt


Configure
---------

Solitude will work without any settings changes at all with zippy, the
reference implementation of the payment provider.

However since solitudes main job is to communicate with remote payment
providers you will need to configure those. To do so create a settings file.

Create an empty settings::

    cd solitude/settings
    echo "from . import base" > local.py

Environment settings
~~~~~~~~~~~~~~~~~~~~

Out of the box, zamboni should work without any need for settings changes. A
few settings are configurable from the environment, they are:

* ``DATABASE``: from the ``SOLITUDE_DATABASE`` environment variable, configured
  using https://github.com/kennethreitz/dj-database-url. Example and default::

    export ZAMBONI_DATABASE=mysql://root:@localhostyy:3306/zamboni

* ``MEMCACHE_URL``: from the ``MEMCACHE_URL`` environment variable, example::

    export MEMCACHE_URL=localhost:11211

* ``SOLITUDE_PROXY``: from the ``SOLITUDE_PROXY`` environment variable. Set
  this to 'enabled' to turn on the solitude proxy. Example::

    export SOLITUDE_PROXY=enabled

PayPal settings
~~~~~~~~~~~~~~~

.. note:: PayPal is there in the code, but has not been used in production.

Having solitude communicate with PayPal can be a slow and cumbersome. To speed
it up you can just mock out all of PayPal::

    PAYPAL_MOCK = True

This assumes a happy path, where everything works. Most things are implemented
for the mock.

To actually talk to PayPal you'll need to setup the following settings. These
are the settings for the Sandbox, meaning you can test Solitude without using
real money::

    PAYPAL_USE_SANDBOX = True
    PAYPAL_APP_ID = 'the.app.id.from.paypal'
    PAYPAL_AUTH = {'USER': 'the.paypal.user',
                   'PASSWORD': 'the.paypal.password',
                   'SIGNATURE': 'the.paypal.signature'}

To do this you will need a PayPal developer account. Go to
developer.paypal.com_ and create an account. This is your developer account,
not the sandbox account.

Once you are logged into developer.paypal.com_ go to `Test Accounts` > `Create
a preconfigured account`. Make sure account type is `seller`. Remember your
password (or set it something really easy). Click `Create Account`.

Then click on `API and Payment Card Credentials`. You will see the `API
Username`, `API Password` and `Signature` fields for that account. Enter those
details into the `PAYPAL_AUTH` setting.

You can repeat this process to create buyer and seller accounts. They must all
be different.

Currently `PAYPAL_APP_ID` is specific to our sandbox. Ask someone in the
marketplace team for the sandbox version.

Solitude creates redirects through PayPal. To make sure Solitude doesn't do
a redirect to some nasty site, we whitelist URLs. On the dev server at Mozilla
it's set to the following. You'll want to set these URLs to match whatever
front end site is using Solitude::

    PAYPAL_URL_WHITELIST = ('https://marketplace-dev.allizom.org',)

Bango settings
~~~~~~~~~~~~~~

To process payments with Bango, you will need a Bango account. Once you have
that, setup your account details::

    BANGO_AUTH = {'USER': 'the.bango.username',
                  'PASSWORD': 'the.bango.password'}

Solitude also receives requests from Bango. Bango needs to know a URL and a
username and password for them. Example::

    BANGO_BASIC_AUTH = {'USER': 'a.username',
                        'PASSWORD': 'a.password'}
    BANGO_NOTIFICATION_URL = 'https://your.site/notification'

These are passed to Bango each time a package is created.

You can fake out Bango for some tasks if you'd like::

    BANGO_MOCK = True

Boku settings
~~~~~~~~~~~~~

To process payments with Boku, you will need a Boku account. Once you have
that, setup your account details::

    BOKU_SECRET_KEY = 'your-secret-key'
    BOKU_MERCHANT_ID = 'your-merchant-id'

You can fake out Boku for some tasks if you'd like::

    BOKU_MOCK = True

Zippy settings
~~~~~~~~~~~~~~

Solitude supports zippy by default. If you'd like to use a server other
than paas, then alter `ZIPPY_CONFIGURATION`, for example::

    ZIPPY_CONFIGURATION = {
        'reference': {
            'url': 'http://localhost:8080',
            'auth': {'key': 'a.key',
                     'secret': 'a.secret',
                     'realm': 'a.realm'}
        }
    }

* `reference`: this is the name of the zippy implementation. Its used as
  the key for the URLs.
* `url`: the location of the zippy server.
* `auth`: the key, secret and realm used for calculating the oAuth. Zippy must
  have the same configuration.

Running Locally
~~~~~~~~~~~~~~~

Create the database using the same name from settings::

    mysql -u root -e 'create database solitude'

Then run::

    schematic migrations

This should set up your database.

Now you can generate previously configured `.key` files::

    python manage.py generate_aes_keys

If you can run the server by doing the following::

    python manage.py runserver localhost:9000

And then::

    curl http://localhost:9000/services/status/

You should get a response similar to this:

.. code-block:: javascript

    {
        "cache": true,
        "proxies": true,
        "db": true,
        "settings": true
    }

Optional settings
-----------------

* **DUMP_REQUESTS**: `True` or `False`. Will dump to the `s.dump` log:
  incoming requests, outgoing requests and incoming responses.

* **CLEANSED_SETTINGS_ACCESS**: `True` or `False`. Will give you access to the
  cleansed settings in the `django.conf.settings` through the API. Should be
  `False` on production.

Getting a traceback in development
----------------------------------

There are too many options for this, but it's a commonly asked question.

First off ensure your logs are going somewhere::

    LOGGING = {
            'loggers': {
                    'django.request.tastypie': {
                            'handlers': ['console'],
                            'level': 'DEBUG',
                    },
            },
    }


Option 1 (recommended)
~~~~~~~~~~~~~~~~~~~~~~

Get a nice response in the client and something in the server console. Set::

    DEBUG = True
    DEBUG_PROPAGATE_EXCEPTIONS = True
    TASTYPIE_FULL_DEBUG = False

Example from client::

    [master] solitude $ curling -d '{"uuid":"1"}' http://localhost:8001/bango/refund/status/
    {
      "error_data": {},
      "error_code": "ZeroDivisionError",
      "error_message": "integer division or modulo by zero"
    }

And on the server::

    ...
    File "/Users/andy/sandboxes/solitude/lib/bango/resources/refund.py", line 47, in obj_get
        1/0
     :/Users/andy/sandboxes/solitude/solitude/base.py:220
    [03/Feb/2013 08:48:02] "GET /bango/refund/status/ HTTP/1.1" 500 108

Option 2
~~~~~~~~

Get the full traceback in the client and nothing in the console. Set::

    DEBUG = True
    DEBUG_PROPAGATE_EXCEPTIONS = False
    TASTYPIE_FULL_DEBUG = True

On the client::

    [master] solitude $ curling -d '{"uuid":"1"}' http://localhost:8001/bango/refund/status/
    {
            "traceback": [
            ...
            "  File \"/Users/andy/sandboxes/solitude/lib/bango/resources/refund.py\", line 47, in obj_get\n    1/0\n"
            ],
            "type": "<type 'exceptions.ZeroDivisionError'>",
            "value": "integer division or modulo by zero"
    }

Option 3
~~~~~~~~

Get the full response in the server console and just a "error occurred" message
on the client::

    DEBUG = True
    DEBUG_PROPAGATE_EXCEPTIONS = True
    TASTYPIE_FULL_DEBUG = True

.. _homebrew: http://mxcl.github.com/homebrew/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _developer.paypal.com: https://developer.paypal.com
.. _playdoh: http://playdoh.readthedocs.org/en/latest/getting-started/installation.html
