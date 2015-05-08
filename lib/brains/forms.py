from django import forms
from django.core.exceptions import ObjectDoesNotExist

from lib.brains.models import BraintreeBuyer, BraintreePaymentMethod
from lib.buyers.models import Buyer
from lib.sellers.models import SellerProduct
from solitude.related_fields import PathRelatedFormField


class BuyerForm(forms.Form):
    uuid = forms.CharField(max_length=255)

    def clean_uuid(self):
        data = self.cleaned_data

        try:
            self.buyer = Buyer.objects.get(uuid=data['uuid'])
        except ObjectDoesNotExist:
            raise forms.ValidationError('Buyer does not exist.')

        if BraintreeBuyer.objects.filter(buyer=self.buyer).exists():
            raise forms.ValidationError('Braintree buyer already exists.')

        return data


class PaymentMethodForm(forms.Form):
    buyer_uuid = forms.CharField(max_length=255)
    nonce = forms.CharField(max_length=255)

    def clean_buyer_uuid(self):
        data = self.cleaned_data

        try:
            self.buyer = Buyer.objects.get(uuid=data['buyer_uuid'])
        except ObjectDoesNotExist:
            raise forms.ValidationError('Buyer does not exist.')

        try:
            self.braintree_buyer = self.buyer.braintreebuyer
        except ObjectDoesNotExist:
            raise forms.ValidationError('Braintree buyer does not exist.')

        return data

    @property
    def braintree_data(self):
        return {
            'customer_id': str(self.braintree_buyer.braintree_id),
            'payment_method_nonce': self.cleaned_data['nonce'],
            # This will force the card to be verified upon creation.
            'options': {
                'verify_card': True
            }
        }


class SubscriptionForm(forms.Form):
    paymethod = PathRelatedFormField(
        view_name='braintree:mozilla:paymethod-detail',
        queryset=BraintreePaymentMethod.objects.filter())
    plan = forms.CharField(max_length=255)

    def clean(self):
        data = self.cleaned_data

        try:
            obj = SellerProduct.objects.get(external_id=data['plan'])
        except ObjectDoesNotExist:
            raise forms.ValidationError('Seller product does not exist.')

        self.seller_product = obj
        return data

    @property
    def braintree_data(self):
        return {
            'payment_method_token': self.cleaned_data['paymethod'].provider_id,
            'plan_id': self.seller_product.external_id,
            'trial_period': False,
            'name': 'Mozilla',
        }
