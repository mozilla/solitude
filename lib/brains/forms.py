from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import requests
from braintree.exceptions.not_found_error import NotFoundError

from lib.brains.client import get_client
from lib.brains.errors import BraintreeResultError
from lib.brains.models import BraintreeBuyer, BraintreePaymentMethod
from lib.buyers.models import Buyer
from lib.sellers.models import SellerProduct
from payments_config import products
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

        # Ideally this should be limited by the type of method
        # as well, something we'll need to remember when we add in another
        # payment method. However, we don't know the type until the reply
        # comes from Braintree.
        if (self.braintree_buyer.braintreepaymentmethod_set
                .filter(active=True).count()
                >= settings.BRAINTREE_MAX_METHODS):
            raise forms.ValidationError(
                'Reached maximum number of payment methods',
                code='max_size')

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
            log.info(
                'no seller product with braintree plan id: {plan}'
                .format(plan=data))
            raise forms.ValidationError(
                'Seller product does not exist.', code='does_not_exist')

        self.seller_product = obj
        return data

    def format_descriptor(self, name):
        # The rules for descriptor are:
        #
        # Company name/DBA section must be either 3, 7 or 12 characters and
        # the product descriptor can be up to 18, 14, or 9 characters
        # respectively (with an * in between for a total descriptor
        # name of 22 characters)
        return 'Mozilla*{}'.format(name)[0:22]

    def get_name(self, plan_id):
        if plan_id in products:
            return unicode(products.get(plan_id).description)
        log.warning('Unknown product for descriptor: {}'.format(plan_id))
        return 'Product'

    @property
    def braintree_data(self):
        plan_id = self.seller_product.public_id
        return {
            'payment_method_token': self.cleaned_data['paymethod'].provider_id,
            'plan_id': plan_id,
            'trial_period': False,
            'descriptor': {
                'name': self.format_descriptor(self.get_name(plan_id)),
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


class PayMethodUpdateForm(forms.Form):
    active = forms.BooleanField(required=False)

    def __init__(self, data, obj):
        self.object = obj
        return super(PayMethodUpdateForm, self).__init__(data)

    def clean_active(self):
        active = self.cleaned_data['active']

        # An attempt to enable active on the payment method.
        if active and not self.object.active:
            raise forms.ValidationError(
                'Cannot set an inactive payment method to active',
                code='invalid')

        # Disabling a payment method.
        #
        # Deletes the payment method from Braintree. See:
        # http://bit.ly/1g82b0Q for more.
        if not active and self.object.active:
            log.info('Payment method set inactive in solitude: {}'
                     .format(self.object.pk))
            client = get_client().PaymentMethod
            try:
                result = client.delete(self.object.provider_id)
                if not result.is_success:
                    log.warning('Error on deleting Payment method: {} {}'
                                .format(self.object.pk, result.message))
                    raise BraintreeResultError(result)
            except NotFoundError:
                # Repeated deletes hit a NotFoundError, if we assume that
                # deletes should be idempotent, we can catch and ignore this.
                log.info('Payment method not found: {}'.format(self.object.pk))
                return

            log.info('Payment method deleted from braintree: {}'
                     .format(self.object.pk))

        return active
