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
  that resource. Example: `123`. Please note that some
  endpoints return a value of `confirm_pin` or similar, that's
  `a bug <https://github.com/mozilla/solitude/issues/380>`_.

* `response_uri` (string): a URI to the object within solitude. To turn it
  into a URL add the protocol and domain of the server. Example:
  `/generic/transaction/123/`. To turn that into URL:
  `http://solitude:2602/generic/transaction/123/`. Note: that some endpoints
  return a value of `no_uri`, or similar, that's
  `a bug <https://github.com/mozilla/solitude/issues/380>`_.


Errors
~~~~~~

Errors. Consistent interface to be determined
`by this issue <https://github.com/mozilla/solitude/issues/349>`_.
