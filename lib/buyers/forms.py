from django import forms
from .models import Buyer


class BuyerValidation(forms.ModelForm):

    class Meta:
        model = Buyer
