.. _setup.rst:

==============
Setup
==============

This is a standard Django or Playdoh project so the setup should be pretty
straight forward. Requirements:

* MySQL
* Python 2.6 or 2.7

For more information see the playdoh_ installation docs.

Requirements
------------

If you don't have Python or MySQL installed. On OS X, homebrew_ is
recommended::

        brew install python mysql

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

Setup settings::

        cd solitude/settings
        cp local.py-dist local.py

Now edit the `local.py` settings. In your favourite text editor. Example
settings::

        SECRET_KEY ='enter.some.string.here'
        if not base.DATABASES:
            DATABASES = {
                   'default': {
                            'ENGINE': 'django.db.backends.mysql',
                            'NAME': 'solitude',
                            'USER': 'root',
                            'PASSWORD': '',
                            'HOST': '',
                            'PORT': '',
                            'OPTIONS': {
                                    'init_command': 'SET storage_engine=InnoDB',
                                    'charset' : 'utf8',
                                    'use_unicode' : True,
                            },
                            'TEST_CHARSET': 'utf8',
                            'TEST_COLLATION': 'utf8_general_ci',
                    },
            }

        STATSD_CLIENT = 'django_statsd.clients.null'
        CLEANSED_SETTINGS_ACCESS = True
        PAYPAL_USE_SANDBOX = True

Solitude requires some keys on the file system. For each key in `base.py`,
copy into `local.py` and point to a file that makes sense for your install. For
example::

        AES_KEYS = {
            # For the purposes of testing, let's set these to the same
            # values.
            'buyerpaypal:key': 'foo.key',
            'sellerpaypal:id': 'foo.key',
            'sellerpaypal:token': 'foo.key',
            'sellerpaypal:secret': 'foo.key',
            'sellerproduct:secret': 'foo.key',
            'bango:signature': 'foo.key',
        }

Then run::

        python manage.py generate_aes_keys

PayPal settings
~~~~~~~~~~~~~~~

Having solitude communicate with PayPal can be a slow and cumbersome. To speed
it up you can just mock out all of PayPal::

        PAYPAL_MOCK = True

This assumes a happy path, where everything works. Most things are implemented
for the mock.

To actually talk to PayPal you'll need to setup the following settings. These
are the settings for the Sandbox, meaning you can test Solitude without using
real money::


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

Having solitude communicate with Bango can be a slow and cumbersome. To speed
it up you can just mock out all of Bango::

        BANGO_MOCK = True

This assumes a happy path, where everything works. To actually talk to Bango
you'll have need to setup the following::

        BANGO_AUTH = {'USER': 'the.bango.username',
                      'PASSWORD': 'the.bango.password'}

Running Locally
~~~~~~~~~~~~~~~

Create the database using the same name from settings::

    mysql -u root -e 'create database solitude'

Then run::

        schematic migrations

This should set up your database.

If you can run the server by doing the following::

        python manage.py runserver localhost:9000

And then::

        curl http://localhost:9000/services/

You should get a response like this::

        {"error": {"list_endpoint": "/services/error/",
                   "schema": "/services/error/schema/"},
         "settings": {"list_endpoint": "/services/settings/",
                      "schema": "/services/settings/schema/"}
        }

Running on Stackato
~~~~~~~~~~~~~~~~~~~

Note: If you have an old ``solitude/settings/local.py`` that defines
DATABASES unconditionally, you will need to modify it, since Stackato
supplies its own database config.

To deploy your Solitude config on Stackato, first install the `Stackato
client <http://www.activestate.com/stackato/download_client>`_.

then run:

``stackato target https://api.paas.allizom.org/``

``stackato login`` (use your LDAP credentials)

After a successful login, ``stackato push --path . my-solitude`` will
upload your app and start it. (``my-solitude`` is an example name, use
a name that makes sense for your deployment.) Leave the prompt for
domain name blank, accepting the default. The command should result in
a log of the install/deploy process and end with the url your service
is now available at. You can use ``stackato ssh my-solitude`` to
connect to the VM running your app. Logs are stored in ``/app/logs``.

When done, you can run ``stackato delete my-solitude`` to remove your VM.

For more docs on the Stackato tools, see the
`Stackato docs site <https://api.paas.allizom.org/docs/client/index.html>`_.

Optional settings
-----------------

* **DUMP_REQUESTS**: `True` or `False`. Will dump the incoming requests for std out.
  Use this for development. For extra excitement install curlish_ to get
  coloured output. Curlish is a really nice way to interact with the solitude
  as a client as well.

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
        DEBUG_PROPAGATE_EXCEPTIONS = False
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

.. _curlish: http://pypi.python.org/pypi/curlish/
.. _homebrew: http://mxcl.github.com/homebrew/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _developer.paypal.com: https://developer.paypal.com
.. _playdoh: http://playdoh.readthedocs.org/en/latest/getting-started/installation.html
