from .constants import PAYPAL_CURRENCIES


class PaypalError(Exception):
    # The generic Paypal error and message.
    def __init__(self, message='', id=None, data=None):
        super(PaypalError, self).__init__(message)
        self.id = str(id)
        self.data = data or {}
        self.default = ('There was an error communicating with PayPal. '
                        'Please try again later.')

    def __str__(self):
        msg = self.message
        return msg.encode('utf8') if isinstance(msg, unicode) else msg


class PaypalDataError(PaypalError):
    # Some of the data passed to Paypal was incorrect. We'll catch them and
    # re-raise as a PaypalError so they can be easily caught.
    pass


class AuthError(PaypalError):
    # We've got the settings wrong on our end.
    pass


class PreApprovalError(PaypalError):
    # Something went wrong in pre approval, there's usually not much
    # we can do about this.
    pass


class CurrencyError(PaypalError):
    # This currency was bad.

    def __str__(self):
        return PAYPAL_CURRENCIES.get(self.data.get('currency', ''),
                                     'Unknown currency')


errors = {'default': {'520003': AuthError}}
# If you want to group errors from PayPal together into groups, this is the
# place to add them in for each PayPal call.
errors['get-pay-key'] = errors['default'].copy()

# See http://bit.ly/vWV525 for information on these values.
# Note that if you have and invalid preapproval key you get 580022, but this
# also occurs in other cases so don't assume its preapproval only.
for number in ['569017', '569018', '569019', '569016', '579014', '579024',
               '579025', '579026', '579027', '579028', '579030', '579031']:
    errors['get-pay-key'][number] = PreApprovalError

for number in ['580027', '580022']:
    errors['get-pay-key'][number] = CurrencyError
