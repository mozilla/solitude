.. _ipn:

===
IPN
===

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
