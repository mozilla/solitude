from django import forms

from django_paranoia.forms import ParanoidForm, ParanoidModelForm
from tastypie.validation import FormValidation

from .models import Buyer


class PinMixin(object):
    def clean_pin(self):
        pin = self.cleaned_data['pin']

        if pin is None or len(pin) == 0:
            return pin

        if not len(pin) == 4:
            raise forms.ValidationError('PIN must be exactly 4 numbers long')

        if not pin.isdigit():
            raise forms.ValidationError('PIN may only consists of numbers')

        return pin


class BuyerForm(ParanoidModelForm, PinMixin):

    class Meta:
        model = Buyer


class PinForm(ParanoidForm, PinMixin):
    uuid = forms.CharField(required=True)
    pin = forms.CharField(required=True)


class BuyerFormValidation(FormValidation):
    def is_valid(self, bundle, request=None):
        data = bundle.data
        if data is None:
            data = {}
        if bundle.obj:
            form = self.form_class(data, instance=bundle.obj)
        else:
            form = self.form_class(data)
        if form.is_valid():
            return {}
        return form.errors
