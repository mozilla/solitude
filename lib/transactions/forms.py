from datetime import datetime, timedelta

from django import forms
from django.conf import settings

import commonware.log
from django_paranoia.forms import ParanoidForm

from lib.transactions import constants
from lib.transactions.constants import STATUSES

log = commonware.log.getLogger('s.transaction')


def check_status(old, new):
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


class UpdateForm(ParanoidForm):
    notes = forms.CharField(required=False)
    status = forms.ChoiceField(choices=[(v, v) for v in STATUSES.values()],
                               required=False)
    uid_pay = forms.CharField(required=False)

    def __init__(self, *args, **kw):
        self.old = kw.pop('original_data')
        super(UpdateForm, self).__init__(*args, **kw)

    def clean(self):
        keys = set(self.data.keys()).difference(set(self.fields.keys()))
        if keys:
            raise forms.ValidationError(
                'Cannot alter fields: {0}'.format(', '.join(keys)))

        check_status(self.old, self.data)
        return self.cleaned_data
