import base64
import hmac
import hashlib
import re
import time

x = re.compile(r'([A-Za-z0-9_]+)')


def escape(value):
    # PayPal bizarre escaping.
    res = []
    for c in str(value):
        if not x.match(c):
            res.append('%' + hex(ord(c))[2:])
        else:
            res.append(c)
    return ''.join(res)


# TODO: replace this with a damn OAuth library.
def get_auth_header(api_user, api_pass, access_tok, sec_tok,
                    http_method, script_uri):
    timestamp = int(time.time())
    data = (
        ('oauth_consumer_key', api_user),
        ('oauth_signature_method', 'HMAC-SHA1'),
        ('oauth_timestamp', timestamp),
        ('oauth_token', access_tok),
        ('oauth_version', 1.0),
    )
    data = ['%s=%s' % (k, v) for k, v in data]
    data = '&'.join((http_method, escape(script_uri), escape('&'.join(data))))
    key = '&'.join((api_pass, escape(sec_tok)))
    hashed = hmac.new(key, data, hashlib.sha1)
    return str(timestamp), base64.b64encode(hashed.digest())
