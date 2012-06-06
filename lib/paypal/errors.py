class PaypalError(Exception):
    # The generic Paypal error and message.
    def __init__(self, message='', id=None, paypal_data=None):
        super(PaypalError, self).__init__(message)
        self.id = id
        self.paypal_data = paypal_data
        self.default = ('There was an error communicating with PayPal. '
                        'Please try again later.')

    def __str__(self):
        msg = self.message
        #if not msg:
        #    msg = messages.get(self.id, self.default)
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


#class CurrencyError(PaypalError):
    # This currency was bad.

#    def __str__(self):
#        default = _('There was an error with this currency.')
#        if self.paypal_data and 'currencyCode' in self.paypal_data:
#            try:
#                return (messages.get(self.id) %
#                    amo.PAYPAL_CURRENCIES[self.paypal_data['currencyCode']])
#                # TODO: figure this out.
#            except:
#                pass
#        return default


errors = {'520003': AuthError}
# See http://bit.ly/vWV525 for information on these values.
# Note that if you have and invalid preapproval key you get 580022, but this
# also occurs in other cases so don't assume its preapproval only.
for number in ['569017', '569018', '569019', '569016', '579014', '579024',
               '579025', '579026', '579027', '579028', '579030', '579031']:
    errors[number] = PreApprovalError
#for number in ['559044', '580027', '580022']:
#    errors[number] = CurrencyError
