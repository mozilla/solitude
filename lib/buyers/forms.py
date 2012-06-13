from django import forms
from .models import Buyer


class BuyerValidation(forms.ModelForm):

    class Meta:
        model = Buyer


class PreapprovalValidation(forms.Form):
    start = forms.DateField()
    end = forms.DateField()
    return_url = forms.URLField()
    cancel_url = forms.URLField()
