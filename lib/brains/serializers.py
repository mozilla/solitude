from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.brains.models import (
    BraintreeBuyer, BraintreePaymentMethod, BraintreeSubscription,
    BraintreeTransaction)
from lib.buyers.serializers import BuyerSerializer
from lib.transactions import constants
from lib.transactions.serializers import TransactionSerializer
from solitude.base import BaseSerializer
from solitude.related_fields import PathRelatedField


class Namespaced(serializers.Serializer):

    def __init__(self, **kwargs):
        self.serial = kwargs

    @property
    def data(self):
        def traverse(d):
            for k, v in d.iteritems():
                if isinstance(v, dict):
                    traverse(v)
                if isinstance(v, serializers.Serializer):
                    d[k] = v.data

        traverse(self.serial)
        return self.serial


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


class LocalTransaction(BaseSerializer):
    paymethod = PathRelatedField(
        view_name='braintree:mozilla:paymethod-detail', read_only=True)
    subscription = PathRelatedField(
        view_name='braintree:mozilla:subscription-detail', read_only=True)
    transaction = PathRelatedField(
        view_name='generic:transaction-detail', read_only=True)

    class Meta:
        model = BraintreeTransaction
        read_only_fields = (
            'billing_period_end_date', 'billing_period_start_date', 'kind',
            'next_billing_date', 'next_billing_period_amount'
        )

    def resource_uri(self, pk):
        return reverse('braintree:mozilla:transaction-detail',
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


def serialize_webhook(webhook, transaction):
    if transaction.provider != constants.PROVIDER_BRAINTREE:
        raise ValueError('Not a Braintree transaction, got {}'
                         .format(transaction.provider))

    braintree = transaction.braintreetransaction
    serializer = Namespaced(
        mozilla={
            'buyer': BuyerSerializer(transaction.buyer),
            'subscription': LocalSubscription(braintree.subscription),
            'transaction': {
                'generic': TransactionSerializer(transaction),
                'braintree': LocalTransaction(braintree),
            },
            'paymethod': LocalPayMethod(braintree.paymethod),
        },
        braintree={
            'kind': webhook.kind
        }
    )

    return serializer.data
