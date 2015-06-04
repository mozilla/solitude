from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import requests

from lib.brains.models import BraintreeBuyer, BraintreePaymentMethod
from lib.buyers.models import Buyer
from lib.sellers.models import SellerProduct
from solitude.base import getLogger
from solitude.related_fields import PathRelatedFormField

log = getLogger('s.brains')


class BuyerForm(forms.Form):
    uuid = forms.CharField(max_length=255)

    def clean_uuid(self):
        data = self.cleaned_data['uuid']

        try:
            self.buyer = Buyer.objects.get(uuid=data)
        except ObjectDoesNotExist:
            raise forms.ValidationError('Buyer does not exist.',
                                        code='does_not_exist')

        if BraintreeBuyer.objects.filter(buyer=self.buyer).exists():
            raise forms.ValidationError('Braintree buyer already exists.',
                                        code='already_exists')

        return data


class PaymentMethodForm(forms.Form):
    buyer_uuid = forms.CharField(max_length=255)
    nonce = forms.CharField(max_length=255)

    def clean_buyer_uuid(self):
        data = self.cleaned_data['buyer_uuid']

        try:
            self.buyer = Buyer.objects.get(uuid=data)
        except ObjectDoesNotExist:
            raise forms.ValidationError('Buyer does not exist.',
                                        code='does_not_exist')

        try:
            self.braintree_buyer = self.buyer.braintreebuyer
        except ObjectDoesNotExist:
            raise forms.ValidationError('Braintree buyer does not exist.',
                                        code='does_not_exist')

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

    def clean_plan(self):
        data = self.cleaned_data['plan']

        try:
            obj = SellerProduct.objects.get(public_id=data)
        except ObjectDoesNotExist:
            raise forms.ValidationError(
                'Seller product does not exist.', code='does_not_exist')

        self.seller_product = obj
        return data

    @property
    def braintree_data(self):
        return {
            'payment_method_token': self.cleaned_data['paymethod'].provider_id,
            'plan_id': self.seller_product.public_id,
            'trial_period': False,
            'descriptor': {
                # TODO: figure out how to get product in here
                # https://github.com/mozilla/payments/issues/57
                'name': 'Mozilla*product',
                'url': 'mozilla.org'
            }
        }


class WebhookVerifyForm(forms.Form):
    bt_challenge = forms.CharField()

    @property
    def braintree_data(self):
        return self.cleaned_data['bt_challenge']

    def clean_bt_challenge(self):
        res = requests.get(
            settings.BRAINTREE_PROXY + '/verify',
            params={'bt_challenge': self.cleaned_data['bt_challenge']}
        )
        if res.status_code != 200:
            log.error('Did not receive a 204 from solitude-auth, got: {}'
                      .format(res.status_code))
            raise forms.ValidationError(
                'Did not pass verification', code='invalid')
        self.response = res.content
        return self.cleaned_data['bt_challenge']


class WebhookParseForm(forms.Form):
    bt_signature = forms.CharField()
    bt_payload = forms.CharField()

    @property
    def braintree_data(self):
        return (
            self.cleaned_data['bt_signature'],
            self.cleaned_data['bt_payload']
        )

    def clean(self):
        res = requests.post(settings.BRAINTREE_PROXY + '/parse', self.data)
        if res.status_code != 204:
            log.error('Did not receive a 204 from solitude-auth, got: {}'
                      .format(res.status_code))
            raise forms.ValidationError(
                'Did not pass verification', code='invalid')
        return self.cleaned_data
