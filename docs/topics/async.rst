.. _async:

===============
Async
===============

Most of the requests that Solitude makes to external servers can be slow.
Solitude can make requests async if you'd like. To find out when the request
has been completed, you need to poll the server [#]_.

To make *POST*, *PUT* or *PATCH* async send the HTTP header:

* **Solitude-Async**: yes (or any non empty value)

When Solitude receives this, it will place the request into the async queue and
return you a 202 status code. Along with the polling URLs (in JSON)::

        {"replay": "/delay/replay/ca8027fe-3570-4e70-8313-00e81ce8432d/",
         "result": "/delay/result/ca8027fe-3570-4e70-8313-00e81ce8432d/"}

If you query the result URL you'll be told the status of the method. If it's
a 404 then it has not been processed yet. The result will return you the status
of the task::

        {"content": "...",
         "id": "1",
         ...
         "run": true,
         "status_code": 201}

In this case our task has been run and returned a status code of 201. The
result of the call is in content. This can be a little inconvenient to use, so
you can do this by the replay url. You'll get back a response that
matches what you would have using the non-sync API. In this case you get
a response with the status code of 201 and the content::

        {"paypal": null,
         "pin": false,
         "resource_pk": 1,
         "resource_uri": "/generic/buyer/1/",
         "uuid": "some:uid"}

To differentiate between differences obtaining the replay record and the actual
record, there is a HTTP header sent with a replay to tell you if the replay was
run or not:

* **Solitude-Async**: yes (the task was run you are getting the real result) or
  no (the task was not run).

For example if the real task returned a 404, without checking this header its
impossible to distinguish that and a task that doesn't exist.

.. [#] Callbacks are better, but there are network issues with Solitude
       making requests.
