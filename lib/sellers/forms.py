from django import forms
from .models import Seller, SellerPaypal, SellerBluevia


class SellerValidation(forms.ModelForm):

    class Meta:
        model = Seller


class SellerPaypalValidation(forms.ModelForm):

    class Meta:
        model = SellerPaypal
        exclude = ['seller', 'token', 'secret']


class SellerBlueviaValidation(forms.ModelForm):

    class Meta:
        model = SellerBluevia
        exclude = ['seller']
