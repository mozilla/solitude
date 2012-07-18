.. _pay:

========================
Pay API
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
