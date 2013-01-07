from django import forms

from django_paranoia.forms import ParanoidForm, ParanoidModelForm
from tastypie.validation import FormValidation

from .field import FormHashField
from .models import Buyer


def base_clean_pin(form, field_name='pin'):
    pin = form.cleaned_data[field_name]

    # pin will be a boolean if it was filled in by tastypie using the
    # dehydrate method. I wrote a custom FormHashField that will pass
    # the bool along if tastypie sent it, is so we can tell the
    # difference between tastypie doing this or someone typing "True"
    # into the PIN entry.
    if isinstance(pin, bool):
        return form.instance.pin

    if pin is None or len(pin) == 0:
        return pin

    if not len(pin) == 4:
        raise forms.ValidationError('PIN must be exactly 4 numbers long')

    if not pin.isdigit():
        raise forms.ValidationError('PIN may only consists of numbers')

    return pin


class PinMixin(object):
    def clean_pin(self):
        return base_clean_pin(self)

    def clean_new_pin(self):
        return base_clean_pin(self, field_name='new_pin')


class BuyerForm(ParanoidModelForm, PinMixin):
    pin = FormHashField(required=False)
    new_pin = FormHashField(required=False)

    class Meta:
        model = Buyer
        exclude = ['pin_locked_out', 'pin_failures']


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
            bundle.data.update(form.cleaned_data)
            return {}
        return form.errors
