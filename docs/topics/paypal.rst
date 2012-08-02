.. _paypal_buyers:

========================
PayPal
========================

Buyers
========================

The PayPal table contains the PayPal specific data for that user. Create it by
a POST::

        POST /paypal/buyer/
        {"buyer": "/generic/buyer/64/"}

Now you can check that element individually or the root buyer object.

Because the pre-approval key is sensitive, we'll only return True or False that
it exists, not its contents::

        GET /generic/buyer/64/

Returns::

        {u'paypal':
                {u'buyer': u'/generic/buyer/64/',
                 u'currency': None,
                 u'resource_uri': u'/paypal/buyer/64/',
                 u'key': False,
                 u'expiry': None},
         u'uuid': u'59138729-bcb2-420d-ac25-83f5521d12d4',
         u'resource_uri': u'/generic/buyer/66/'}

Now the `paypal` field of the buyer data is populated with the PayPal data.

Sellers
========================

The PayPal table contains the PayPal specific data for that seller. Create it by
a POST::

        POST /paypal/seller/
        {"seller": "/generic/seller/9/",
         "paypal_id": "foo@bar.com"}

Now you can check that element individually or the root seller object.

Because the pre-approval key is sensitive, we'll only return True or False that
it exists, not its contents::

        GET /generic/seller/9/

Returns::

        {u'paypal': {
                u'secret': False,
                u'seller': u'/generic/seller/9/',
                u'paypal_id': u'foo@bar.com',
                u'token': False,
                u'resource_uri': u'/paypal/seller/10/'},
         u'uuid': u'acb21517-df02-4734-8173-176ece310bc1',
         u'resource_uri': u'/generic/seller/9/'}

Now the `paypal` field of the seller data is populated with the PayPal data.

The PayPal seller data supports a PUT for updates.

Pay
========================

This requires a seller with paypal data in solitude.

Start the Pay by doing a POST, passing the required fields::

        POST /paypal/pay/
        {"memo": "foo",
         "cancel_url": "http://solitude.mozilla.ca/cancel.url",
         "seller": "f345b86b-5967-4ab7-8279-07951210641c",
         "currency": "USD",
         "amount": "5",
         "ipn_url": "http://solitude.mozilla.ca/ipn.url",
         "return_url": "http://solitude.mozilla.ca/return.url"}

Fields:

* `cancel_url`: the URL on your site that PayPal will return you to if
  cancelled.
* `buyer` (optional): the buyer uuid. If a pre-approval token exists for the
  buyer, we'll use it.
* `seller`: the seller uuid.
* `ipn_url`: the URL on your site that Paypal will send the IPN too.
* `return_url`: the URL on your site that PayPal will return you to if
  successful.
* `amount`: the amount.
* `currency`: currency as a 3 letter string, see `constants.py`.
* `memo`: a memo for PayPal.
* `uuid` (optional): the transaction id for PayPal, we'll create one if you
  don't specify it.

URLs are whitelisted in solitude so make sure those URLs are in configured in
your settings file with `PAYPAL_URL_WHITELIST`.

If there is no pre-approval, then you'll get back the pay key::

        {u'status': u'CREATED',
         u'pay_key': u'AP-0AS843605E4167253',
         u'resource_uri': u'/paypal/pay/db957c5e-18c5-408b-8882-586a47407317/'}

If there is pre-approval for that buyer and it works, you'll get back
a COMPLETED status::

        {u'status': u'COMPLETED',
         u'pay_key': u'AP-0AS843605E4167253',
         u'resource_uri': u'/paypal/pay/db957c5e-18c5-408b-8882-586a47407317/'}

It will be up to the client to verify that is complete. If the pre-approval
fails you'll get a 500 error.

Pre-approval
========================

This requires a buyer with paypal data in solitude.

Start the PayPal pre-approval by doing a POST, passing the required fields::

        POST /paypal/preapproval/
        {"start": "2012-06-13",
         "cancel_url": "http://solitude.mozilla.ca/cancel.url",
         "end": "2012-07-13",
         "uuid": "21849de8-bec3-4556-849b-a8723a35b5cb",
         "return_url": "http://solitude.mozilla.ca/return.url"}

Fields:

* `start`: when the pre-approval will start.
* `cancel_url`: the URL on your site that PayPal will return you to if
  cancelled.
* `end`: when the pre-approval will end.
* `uuid`: the buyer uuid.
* `return_url`: the URL on your site that PayPal will return you to if
  successful.

URLs are whitelisted in solitude so make sure those URLs are in configured in
your settings file with `PAYPAL_URL_WHITELIST`.

This will return the pre-approval key that you will then pass on to PayPal.
This key should not be stored anywhere. Returns::

        {u'pk': u'f15c7e70-ebe9-49a0-8137-33808ccfde86',
         u'uuid': u'21849de8-bec3-4556-849b-a8723a35b5cb',
         u'key': u'some-key',
         u'resource_uri': u'/paypal/preapproval/f15c7e70-ebe9-49a0-8137-33808ccfde86/'}

When the return is successful, do a PUT back to the pre-approval, this will
make save the key for that user::

        PUT /paypal/preapproval/f15c7e70-ebe9-49a0-8137-33808ccfde86/

The pre-approval key will now be saved for that user.

If the user cancels the pre-approval, do a DELETE to remove the key::

        DELETE /paypal/preapproval/f15c7e70-ebe9-49a0-8137-33808ccfde86/

IPN
===========

When any transaction is processed by PayPal, it will send a request to your
server called an IPN. In all transactions we view the IPN as the definitive
source overriding all other calls.

The client server using solitude must specify and IPN url that PayPal will
call. It's that URL's job to handle the IPN. To handle the IPN send the whole
content to solitude. Solitude will tell you what it did with the IPN and hence
what you should do in your client.

Rough flow:

* Client does a payment, specifying and IPN

* At some point PayPal calls the IPN url in the client

* Client passes IPN data off to solitude

* Solitude confirms the IPN is genuine with PayPal

* Solitude returns a status to the client

* Client handles the IPN appropriately

In the result from solitude you'll get a status and the action that occurred:

* `IPN_STATUS_OK`: the IPN was processed, look at the action to see what happened
  and how it should be processed in your client.

* `IPN_STATUS_IGNORED`: the IPN was ignored. This could be because we've already
  processed the IPN or its not a valid transaction.

* `IPN_STATUS_ERROR`: some other error occurred and the the IPN was not
  processed.

If the status is `IPN_STATUS_OK`, then one of the actions will occur:

* `IPN_ACTION_REFUND`: a refund occurred.

* `IPN_ACTION_PAYMENT`: a payment was successfully processed.

* `IPN_ACTION_REVERSAL`: a payment was reversed (eg chargeback).

The IPN result also returns some data from the transaction so you don't need to
parse the IPN data:

* `uuid`: the uuid for this transaction.

* `amount`: the amount of the transaction.

Proxy
=====

To add a further layer of defense, Solitude can be run in two modes:

* *standalone*: in this case Solitude is only run with **one instance** and
  communicates to PayPal. That one instance knows everything about how to
  interact with the database and has the appropriate settings for communicating
  with PayPal. Requests go **client** > **solitude**
  > **paypal**.

* *proxy*: in this case Solitude is run with **two instances**, a database
  server and proxy server. Requests go **client** > **solitude database server**
  > **solitude proxy server** > **paypal**.

  * *database server* this **can** read and write to the database, the cache and
    so on. It **cannot** talk to PayPal. It has no PayPal username, password or
    any other keys.

  * *proxy server* this **cannot** read and write to the database, the cache
    and so on. It **can** talk to PayPal. It has the PayPal username, password
    and other keys.

By default solitude runs in standalone mode. Running using `runserver` or the
`wsgi/playdoh.py` script will run in this mode.

Running both the database and proxy server on the same instance might not give
you much of an advantage. The intention is to run them in seperate servers and
have appropriate security between them.

To run in proxy mode, make the following changes:

* *database server* ensure you have not specified any sensitive PayPal
  settings. Set `PAYPAL_PROXY` to point to the *proxy server* referencing the
  path `/proxy/paypal` for example::

        PAYPAL_PROXY = 'https://addons.mozilla.local/proxy/paypal'

* *proxy server* ensure you have not specified any database or cache settings,
  but have specified the PayPal settings, such as username, password, sandbox
  and so on.

To run the proxy server, run with the environment variable::

        SOLITUDE_PROXY='enabled'

To run as a wsgi file, just use `wsgi/proxy.py` and it will set this variable
for you.

Mock
====

There's a mock for PayPal that allows zamboni and solitude to interact. Records
are created, updated and deleted in solitude as the process happens. It does
without ever actually calling PayPal. This means that payments will work
automatically as if the user had pre-approved payments (even if they haven't).

Flipping between the mock and using PayPal will generate issues. For example,
the mock will create a fake pre-approval token. If you then use PayPal, that
token will just generate errors.

To use the mock set::

        PAYPAL_MOCK = True
