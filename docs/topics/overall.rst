Overall
-------

There are things that are assumed to be true on all API requests to solitude.
And to prevent repetition in the documentation are mentioned here.

Requests
~~~~~~~~

* It's assumed that all requests are `application/json`. This isn't enforced
  yet, but could be. If you use curling, all requests are sent with
  `Content-Type: application/json`.

* All requests should include `Accept: application/json`. If you use curling
  this is the case.

Responses
~~~~~~~~~

* It's assumed that all responses are `application/json`.

* Where possible we use standard HTTP error status codes, e.g 404. If there is
  anything unusual in the responses, we document those in the specific API
  calls.

Common elements in some responses:

* `response_pk` (string): a primary key for that resource. Will be unique to
  that resource. Example: `123`.

* `response_uri` (string): a URI to the object within solitude. To turn it
  into a URL add the protocol and domain of the server. Example:
  `/generic/transaction/123/`. To turn that into URL:
  `http://solitude:2602/generic/transaction/123/`.

* `created` (datetime): when the object is created. Using the Django Rest
  Framework format, `ECMA 262 <http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15>`_.

* `counter` (int): a counter that increments on each save of an object. This is
  used for etag generation.

* `modified` (datetime): when the object was last modified. Using the Django Rest
  Framework format, `ECMA 262 <http://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15>`_.


Errors
~~~~~~

Errors. Consistent interface in progress and tracked
`by this issue <https://github.com/mozilla/solitude/issues/349>`_.

To seperate the old and new style, two different kinds of errors will be returned
a status of `400 <http://httpstatus.es/400>`_ for old format errors and
`422 <http://httpstatus.es/422>`_ for new format errors.

400
===

Responses are currently inconsistent and pending upon
fixes to Bango and `upgrading to Django Rest Framework 3.x <https://github.com/mozilla/solitude/issues/416>`_.

422
===

Errors will be raised with the namespace of the error, currently one of `mozilla`,
`braintree` or `bango` to represent the part of the system that caused the error.

Mozilla
~~~~~~~
Form errors in Solitude are given the namespace `mozilla`.

An error contains the field the error occurred on and the message and code. It is
possible for more than one error to exist on a field. For a consistent interface
use the `code` attribute.

Example failure in form processing::

    .. code:json::

        {
            "mozilla": {
                "name": [
                    {"message": "First error", "code": "first"},
                    {"message": "Second error", "code": "second"}
                ],
                "__all__": [
                    {"message": "Non field error", "code": "non-field"}
                ]
            }
        }

In this example `name` is a field passed in the request. The `__all__` refers
to an error that did not exist on a field.

Braintree
~~~~~~~~~
Data errors in Braintree are given the namespace `braintree`.

An error contains the field the error occurred on and the message and code. It is
possible for more than one error to exist on a field. For a consistent interface use the code
attribute, the `code` attribute is referenced in the
`Braintree documentation <https://developers.braintreepayments.com/javascript+python/reference/general/validation-errors/all>`_

Errors occur on Braintree fields, not fields passed in the request, so the the error
keys do not match request fields.

Braintree has some errors which it doesn't consider validation errors because
they are not specific to a submitted input field. However, Solitude still
displays these as validation errors so that error handling is consistent.

Example failure from Braintree::

    .. code:json::

        {
            "braintree": {
                "payment_method_token": [
                    {"message": "Payment method token is invalid.", "code": "91903"}
                ],
                "__all__": [
                    {"message": "Credit card denied", "code": "2000"}
                ]
            }
        }

If no error can be found solitude will add the message to the response with code of `unknown`, for example::

    .. code:json::

        {
            "braintree": {
                "__all__": [
                    {"message": "Invalid Secure Payment Data", "code": "unknown"}
                ]
            }
        }
