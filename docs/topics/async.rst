.. _async:

Doing Async calls in Solitude
#############################

Most of the requests Solitude makes to external servers can be slow, and thus
when you do query the Solitude API, the resulting requests can also be slow.

Solitude can make requests async if you'd like. To find out when the request
has been completed, you need to poll the server.

To make *POST*, *PUT* or *PATCH* async you need to use the `Solitude-Async`
HTTP header. You need to set its value to `yes` (or to any non empty value).

When Solitude receives this, it will place the request into the async queue and
return a `202 Accepted` status code, along with the polling URLs (in JSON):

.. code-block:: javascript

    {"replay": "/delay/replay/ca8027fe-3570-4e70-8313-00e81ce8432d/",
     "result": "/delay/result/ca8027fe-3570-4e70-8313-00e81ce8432d/"}

If you query the result URL you'll be told the status of the resource. If it's
a `404 Not Found`, it means it has not been processed yet.

The body of the response contains the status of the task:

.. code-block:: javascript

    {"content": "...",
     "id": "1",
     ...
     "run": true,
     "status_code": 201}

In this case, our task has been run and returned a `201 Created` status code.

The result of the call is in the returned content. As this can be a little
inconvenient to use, you can do the same thing using the replay url.

You'll get back a response matching what you would have using the non-sync
API. Here you would get a `201 Created` with the following content:

.. code-block:: javascript

    {"paypal": null,
     "pin": false,
     "resource_pk": 1,
     "resource_uri": "/generic/buyer/1/",
     "uuid": "some:uid"}

To differentiate between the replay record and the actual record, an additional
`Solitude-Async` HTTP header is returned with the response, giving you this
information. It's value can either be `yes` (the task was run, so this is the
real result) or `no` (the task was not run already).

For example, if the real task returned a `404 Not Found`, without checking this
header its impossible to now id that's the real response of the task or if the
task hadn't be processed already.
