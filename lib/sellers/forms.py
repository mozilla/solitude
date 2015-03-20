from django import forms

from solitude.fields import URLField

from .models import Seller, SellerProduct


class SellerValidation(forms.ModelForm):

    class Meta:
        model = Seller


class SellerProductValidation(forms.ModelForm):
    seller = URLField(to='lib.sellers.resources.SellerResource')

    class Meta:
        model = SellerProduct
