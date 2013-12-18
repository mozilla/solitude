import json
import pprint
import requests
import sys


# TODO: rewrite this to use curling?
def call(root, url, method, data):
    method = getattr(requests, method)
    url = root + url
    print 'Calling url:', url
    print 'Request data:'
    pprint.pprint(data)
    data = json.dumps(data)
    result = method(url, data=data,
                    headers={'content-type': 'application/json'})
    print 'Status code:', result.status_code
    if result.status_code not in (200, 201, 202, 204):
        print 'Error:', result.content
        sys.exit()

    if result.content:
        print 'Response data:'
        data = result.json() if callable(result.json) else result.json
        pprint.pprint(data)
        print
        return data

    print


