from django import forms

from lib.boku.constants import CURRENCIES
from lib.transactions.constants import (PROVIDER_BOKU, STATUS_COMPLETED)
from lib.transactions.models import Transaction

from solitude.logger import getLogger

log = getLogger('s.boku')


class BokuForm(forms.Form):
    """
    Boku form fields all have - in them for the field names, which makes them
    hard to process in a Django form. This converts all the - to _.

    It does not check if that causes any conflicts.
    """
    def __init__(self, data=None, files=None, **kwargs):
        data = dict((k.replace('-', '_'), v) for k, v in (data or {}).items())
        super(BokuForm, self).__init__(data=data, files=files, **kwargs)


class EventForm(BokuForm):
    """
    A form to process the data from Boku.

    This filters out the data by whitelisting out the fields we want.
    """
    action = forms.ChoiceField(choices=(['billingresult', 'billingresult'],))
    amount = forms.DecimalField()
    currency = forms.ChoiceField(choices=([k, k] for k in CURRENCIES.keys()))
    # To be validated against Boku.
    sig = forms.CharField(max_length=255)
    # This is the uuid.
    param = forms.CharField(max_length=100)
    # The transaction id from Boku.
    trx_id = forms.CharField(max_length=50)

    def clean(self):
        cleaned_data = super(EventForm, self).clean()
        # TODO: before going any further check the sig and or verify
        # that this is valid as per. bug 987846.
        return cleaned_data

    def clean_param(self):
        # This takes the param, verifies that the transaction exists
        # and returns the transaction as the result.
        uuid = self.cleaned_data['param']

        try:
            trans = Transaction.objects.get(uuid=uuid, provider=PROVIDER_BOKU)
        except Transaction.DoesNotExist:
            log.info('Transaction not found: %s' % uuid)
            raise forms.ValidationError('Transaction not found: %s' % uuid)

        if trans.status == STATUS_COMPLETED:
            raise forms.ValidationError('Transaction completed: %s' % uuid)

        return trans
