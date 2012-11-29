from django import forms
from .models import Seller, SellerPaypal, SellerProduct


class SellerValidation(forms.ModelForm):

    class Meta:
        model = Seller


class SellerPaypalValidation(forms.ModelForm):

    class Meta:
        model = SellerPaypal
        exclude = ['seller', 'token', 'secret']


class SellerProductValidation(forms.ModelForm):

    class Meta:
        model = SellerProduct
        exclude = ['seller']
