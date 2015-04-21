from django import forms
from django.shortcuts import get_object_or_404

from django_paranoia.forms import ParanoidForm

from lib.buyers.constants import PIN_4_NUMBERS_LONG, PIN_ONLY_NUMBERS
from lib.buyers.models import Buyer


def clean_pin(pin):
    if pin is None or len(pin) == 0:
        return pin

    if not len(pin) == 4:
        raise forms.ValidationError(PIN_4_NUMBERS_LONG)

    if not pin.isdigit():
        raise forms.ValidationError(PIN_ONLY_NUMBERS)

    return pin


class PinForm(ParanoidForm):
    uuid = forms.CharField(required=True)
    pin = forms.CharField(required=True)

    def clean_uuid(self):
        self.cleaned_data['buyer'] = get_object_or_404(
            Buyer,
            uuid=self.cleaned_data.get('uuid'))
        return self.cleaned_data['uuid']

    def clean_pin(self):
        return clean_pin(self.cleaned_data.get('pin'))
