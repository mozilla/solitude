from django import forms
from django.core.exceptions import ObjectDoesNotExist

from lib.brains.models import BraintreeBuyer
from lib.buyers.models import Buyer


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
