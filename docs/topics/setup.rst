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
        pip install -r requirements/dev.txt

Setup settings::

        cd solitude/settings
        cp local.py-dist local.py

Now edit the `local.py` settings. In your favourite text editor. Example
settings::

        SECRET_KEY ='enter.some.string.here'

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

Create the database using the same name from settings::

    mysql -u root -e 'create database solitude'

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
            'sellerbluevia:id': 'foo.key',
            'sellerproduct:secret': 'foo.key',
        }

Then run::

        python manage.py generate_aes_keys

Then run::

        python manage.py syncdb

This should set up your database.

PayPal settings
---------------

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

Running
-------

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

Optional settings
-----------------

* **DUMP_REQUESTS**: `True` or `False`. Will dump the incoming requests for std out.
  Use this for development. For extra excitement install curlish_ to get
  coloured output. Curlish is a really nice way to interact with the solitude
  as a client as well.

* **CLEANSED_SETTINGS_ACCESS**: `True` or `False`. Will give you access to the
  cleansed settings in the `django.conf.settings` through the API. Should be
  `False` on production.

* **TASTYPIE_FULL_DEBUG**: `True` or `False`. Set this to `True` in development
  along with `DEBUG` to get lots of tracebacks.

.. _curlish: http://pypi.python.org/pypi/curlish/
.. _homebrew: http://mxcl.github.com/homebrew/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _developer.paypal.com: https://developer.paypal.com
.. _playdoh: http://playdoh.readthedocs.org/en/latest/getting-started/installation.html
