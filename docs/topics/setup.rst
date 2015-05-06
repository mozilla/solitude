.. _setup.rst:

Setup
#####

The recommended way to run solitude is in Docker.


For running solitude in the marketplace environment, we recommend using Docker
and reading the `marketplace docs <https://marketplace.readthedocs.org/en/latest/topics/backend.html>`_.

For running solitude in the Payments for Firefox Accounts, we recommend using
Docker and reading the `payments docs <https://payments.readthedocs.org>`_.

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

Running tests
-------------

To run unit tests::

    python manage.py test

All live server and Braintree integration tests are not run by default. To run
live server and Braintree integration tests::

    LIVE_TESTS=live,braintree python manage.py test

The value of LIVE_TESTS is passed to the `nose args command
<http://nose.readthedocs.org/en/latest/plugins/attrib.html#simple-syntax>`_.

For the Braintree tests to pass, you will need to have setup a Braintree
sandbox account.

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

.. _braintree-settings:

Braintree settings
~~~~~~~~~~~~~~~~~~

To process payments for Braintree, you will need to get a Braintree account.
For development, use a
`Braintree sandbox account <https://sandbox.braintreegateway.com/login>`_.

Then go to Account > My User > API Keys. Alter your configration to read::

    BRAINTREE_MERCHANT_ID = 'your-merchant-id'
    BRAINTREE_PUBLIC_KEY = 'your-public-key'
    BRAINTREE_PRIVATE_KEY = 'your-private-key'

These values can also be set by environment variables.

The Braintree API server is configured by this setting::

    BRAINTREE_ENVIRONMENT = 'sandbox'

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

Optional settings
-----------------

* **DUMP_REQUESTS**: `True` or `False`. Will dump to the `s.dump` log:
  incoming requests, outgoing requests and incoming responses.

* **CLEANSED_SETTINGS_ACCESS**: `True` or `False`. Will give you access to the
  cleansed settings in the `django.conf.settings` through the API. Should be
  `False` on production.

.. _homebrew: http://mxcl.github.com/homebrew/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _playdoh: http://playdoh.readthedocs.org/en/latest/getting-started/installation.html
