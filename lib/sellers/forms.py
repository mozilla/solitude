from django import forms

from .models import Seller, SellerProduct
from solitude.fields import URLField


class SellerValidation(forms.ModelForm):

    class Meta:
        model = Seller


class SellerProductValidation(forms.ModelForm):
    seller = URLField(to='lib.sellers.resources.SellerResource')

    class Meta:
        model = SellerProduct
