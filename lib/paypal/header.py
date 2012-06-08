import base64
import hmac
import hashlib
import time
import urllib


# TODO: replace this with a damn OAuth library.
def get_auth_header(api_user, api_pass, access_tok, sec_tok,
                    http_method, script_uri):
    timestamp = time.time()
    data = {
        'api_pass': sec_tok,
        'http_method': http_method,
        'oauth_consumer_key': api_user,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': timestamp,
        'oauth_token': access_tok,
        'oauth_version': 1.0,
    }
    data = urllib.urlencode(data)
    hashed = hmac.new(api_pass, data, hashlib.sha1)
    return str(timestamp), base64.b64encode(hashed.digest())
