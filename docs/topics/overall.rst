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

Errors. Consistent interface to be determined
`by this issue <https://github.com/mozilla/solitude/issues/349>`_.
