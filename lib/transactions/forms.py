from datetime import datetime, timedelta

from django import forms
from django.conf import settings

from django_paranoia.forms import ParanoidForm

from lib.transactions import constants
from lib.transactions.constants import STATUSES

from solitude.base import log_cef
from solitude.logger import getLogger

log = getLogger('s.transaction')


def check_status(old, new):
    if old['status'] == constants.STATUS_ERRORED:
        raise forms.ValidationError('Transaction errored')

    if ((old['created'] + timedelta(seconds=settings.TRANSACTION_LOCKDOWN)) <
            datetime.now()):
        raise forms.ValidationError('Transaction locked down')

    elif old['status'] == constants.STATUS_PENDING:
        return

    elif old['status'] in [constants.STATUS_FAILED, constants.STATUS_CANCELLED,
                           constants.STATUS_CANCELLED]:
        msg = 'Cannot change state: {0}'.format(old['status'])
        log.error(msg)
        raise forms.ValidationError(msg)

    elif (old['status'] in [constants.STATUS_CHECKED,
                            constants.STATUS_RECEIVED]
          and new['status'] not in [constants.STATUS_COMPLETED,
                                    constants.STATUS_FAILED]):
        msg = ('Cannot change state from: {0} to {1}'
               .format(old['status'], new['status']))
        log.error(msg)
        raise forms.ValidationError(msg)

    if new.get('status', None) not in [constants.STATUS_STARTED,
                                       constants.STATUS_ERRORED]:
        if not new.get('provider', old.get('provider')):
            raise forms.ValidationError('Provider must be set')

        if not new.get('seller_product', old.get('seller_product')):
            raise forms.ValidationError('Seller product must be set')


class UpdateForm(ParanoidForm):
    notes = forms.CharField(required=False)
    status = forms.ChoiceField(choices=[(v, v) for v in STATUSES.values()],
                               required=False)
    uid_pay = forms.CharField(required=False)
    pay_url = forms.URLField(required=False)

    def __init__(self, *args, **kw):
        self.request = kw.pop('request')  # Storing request for CEF logs.
        self.old = kw.pop('original_data')
        super(UpdateForm, self).__init__(*args, **kw)

    def clean(self):
        keys = set(self.data.keys()).difference(set(self.fields.keys()))
        if keys:
            raise forms.ValidationError(
                'Cannot alter fields: {0}'.format(', '.join(keys)))

        old_text = constants.STATUSES_INVERTED.get(self.old['status'])
        new_text = constants.STATUSES_INVERTED.get(
            self.data.get('status', self.old['status']))

        try:
            check_status(self.old, self.data)
        except forms.ValidationError:
            log_cef('Transaction change failure', self.request, severity=7,
                    cs6Label='old', cs6=old_text, cs7Label='new', cs7=new_text)
            raise

        if new_text != old_text:
            log_cef('Transaction change success', self.request,
                    cs6Label='old', cs6=old_text, cs7Label='new', cs7=new_text)
        return self.cleaned_data
