from django import forms
from .models import Seller, SellerBluevia, SellerPaypal, SellerProduct


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


class SellerProductValidation(forms.ModelForm):

    class Meta:
        model = SellerProduct
        exclude = ['seller']
