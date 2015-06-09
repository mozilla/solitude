from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.brains.models import (
    BraintreeBuyer, BraintreePaymentMethod, BraintreeSubscription)
from lib.transactions.serializers import TransactionSerializer
from solitude.base import BaseSerializer
from solitude.related_fields import PathRelatedField


class Namespaced(serializers.Serializer):

    """
    A crude namespace serializer that puts data from two sources (local and
    braintree) into dictionaries.
    """

    def __init__(self, mozilla, braintree):
        self.mozilla = mozilla
        self.braintree = braintree

    @property
    def data(self):
        return {
            'mozilla': self.mozilla.data,
            'braintree': self.braintree.data
        }


class LocalReceipt(serializers.Serializer):

    """
    Serialize enough information to send the user a receipt in one go.
    """

    def __init__(self, **kw):
        self.serial = {
            'paymethod': LocalPayMethod(instance=kw['paymethod']),
            'subscription': LocalSubscription(instance=kw['subscription']),
            'transaction': TransactionSerializer(instance=kw['transaction'])
        }

    @property
    def data(self):
        return dict((k, v.data) for k, v in self.serial.items())


class LocalPayMethod(BaseSerializer):
    braintree_buyer = PathRelatedField(
        view_name='braintree:mozilla:buyer-detail')

    class Meta:
        model = BraintreePaymentMethod
        read_only_fields = ('provider_id', 'type',
                            'type_name', 'truncated_id')

    def resource_uri(self, pk):
        return reverse('braintree:mozilla:paymethod-detail', kwargs={'pk': pk})


class LocalBuyer(BaseSerializer):
    buyer = PathRelatedField(view_name='generic:buyer-detail')

    class Meta:
        model = BraintreeBuyer
        read_only = ['braintree_id']

    def resource_uri(self, pk):
        return reverse('braintree:mozilla:buyer-detail', kwargs={'pk': pk})


class LocalSubscription(BaseSerializer):
    paymethod = PathRelatedField(
        view_name='braintree:mozilla:paymethod-detail', read_only=True)
    seller_product = PathRelatedField(
        view_name='generic:sellerproduct-detail', read_only=True)

    class Meta:
        model = BraintreeSubscription
        read_only_fields = ('provider_id',)

    def resource_uri(self, pk):
        return reverse('braintree:mozilla:subscription-detail',
                       kwargs={'pk': pk})


class Braintree(serializers.Serializer):

    def __init__(self, instance=None):
        self.object = instance

    @property
    def data(self):
        res = {}
        for field in self.fields:
            obj = self.object
            for k in field.split('.'):
                obj = getattr(obj, k)
            res[k] = obj
        return res


class PayMethod(Braintree):
    fields = ['token', 'created_at', 'updated_at']


class Customer(Braintree):
    fields = ['id', 'created_at', 'updated_at']


class Subscription(Braintree):
    fields = ['id', 'created_at', 'updated_at']


class Webhook(Braintree):
    fields = [
        'kind',
        'subscription.billing_period_end_date',
        'subscription.billing_period_start_date',
        'subscription.next_billing_date',
        'subscription.next_billing_period_amount',
    ]
