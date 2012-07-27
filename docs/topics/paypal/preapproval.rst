.. _preapproval:

========================
Pre-approval API
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
