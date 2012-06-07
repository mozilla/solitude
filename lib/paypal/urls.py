from django.conf import settings

# These are the root URLs that we use in paypal. Flip PAYPAL_USE_SANDBOX
# to get the appropriate
roots = {
    'services': 'https://svcs.paypal.com/',
    'permissions': 'https://svcs.paypal.com/Permissions/',
    'adaptive': 'https://www.paypal.com/',
    'cgi': 'https://www.paypal.com/cgi-bin/webscr'
}

if settings.PAYPAL_USE_SANDBOX:
    roots = {
        'services': 'https://svcs.sandbox.paypal.com/',
        'permissions': 'https://svcs.sandbox.paypal.com/Permissions/',
        'adaptive': 'https://www.sandbox.paypal.com/',
        'cgi': 'https://www.sandbox.paypal.com/cgi-bin/webscr'
    }

# A mapping of a names to urls.
urls = {
    'get-permission': roots['permissions'] + 'GetPermissions',
    'request-permission': roots['permissions'] + 'RequestPermissions',
    'grant-permission': roots['cgi'] + '?cmd=_grant-permission&request_token=',
}
