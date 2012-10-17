from django import forms
from tastypie.validation import FormValidation

from .models import Buyer


class BuyerValidation(forms.ModelForm):

    class Meta:
        model = Buyer


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
