from django.conf import settings

# These are the root URLs that we use in paypal. Flip PAYPAL_USE_SANDBOX
# to get the appropriate
roots = {
    'services': 'https://svcs.paypal.com/',
    'permissions': 'https://svcs.paypal.com/Permissions/',
    'pay': 'https://svcs.paypal.com/AdaptivePayments/',
    'adaptive': 'https://www.paypal.com/',
    'cgi': 'https://www.paypal.com/cgi-bin/webscr'
}

if settings.PAYPAL_USE_SANDBOX:
    roots = {
        'services': 'https://svcs.sandbox.paypal.com/',
        'permissions': 'https://svcs.sandbox.paypal.com/Permissions/',
        'pay': 'https://svcs.sandbox.paypal.com/AdaptivePayments/',
        'adaptive': 'https://www.sandbox.paypal.com/',
        'cgi': 'https://www.sandbox.paypal.com/cgi-bin/webscr'
    }

# A mapping of a names to urls.
urls = {
    'get-permission': roots['permissions'] + 'GetPermissions',
    'request-permission': roots['permissions'] + 'RequestPermissions',
    'get-permission-token': roots['permissions'] + 'GetAccessToken',
    'get-preapproval-key': roots['pay'] + 'Preapproval',
    'get-pay-key': roots['pay'] + 'Pay',
    'grant-permission': roots['cgi'] + '?cmd=_grant-permission&request_token=',
}
