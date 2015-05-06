from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.brains.models import BraintreeBuyer, BraintreePaymentMethod
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


class Braintree(serializers.Serializer):

    def __init__(self, instance=None):
        self.object = instance

    @property
    def data(self):
        return dict([k, getattr(self.object, k)] for k in self.fields)


class PayMethod(Braintree):
    fields = ['token', 'created_at', 'updated_at']


class Customer(Braintree):
    fields = ['id', 'created_at', 'updated_at']
