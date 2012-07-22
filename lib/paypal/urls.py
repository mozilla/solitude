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
        'accounts': 'https://svcs.sandbox.paypal.com/AdaptiveAccounts/',
        'adaptive': 'https://www.sandbox.paypal.com/',
        'cgi': 'https://www.sandbox.paypal.com/cgi-bin/webscr'
    }

# A mapping of a names to urls.
urls = {
    'check-purchase': roots['pay'] + 'PaymentDetails',
    'get-pay-key': roots['pay'] + 'Pay',
    'get-permission': roots['permissions'] + 'GetPermissions',
    'get-permission-token': roots['permissions'] + 'GetAccessToken',
    'get-personal': roots['permissions'] + 'GetBasicPersonalData',
    'get-personal-advanced': roots['permissions'] + 'GetAdvancedPersonalData',
    'get-preapproval-key': roots['pay'] + 'Preapproval',
    'grant-preapproval': roots['cgi'] + '?cmd=_ap-preapproval&preapprovalkey=',
    'get-refund': roots['pay'] + 'Refund',
    'get-verified': roots['accounts'] + 'GetVerifiedStatus',
    'grant-permission': roots['cgi'] + '?cmd=_grant-permission&request_token=',
    'request-permission': roots['permissions'] + 'RequestPermissions',
    'ipn': roots['cgi'],
}
