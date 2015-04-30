from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.brains.models import BraintreeBuyer
from solitude.base import BaseSerializer
from solitude.related_fields import PathRelatedField


class BraintreeBuyerSerializer(BaseSerializer):
    buyer = PathRelatedField(view_name='braintree:buyer-detail')

    class Meta:
        model = BraintreeBuyer
        read_only = ['braintree_id']

    def resource_uri(self, pk):
        return reverse('braintree:buyer-detail', kwargs={'pk': pk})


class BraintreeSerializer(serializers.Serializer):

    def __init__(self, instance=None):
        self.object = instance

    @property
    def data(self):
        return dict([k, getattr(self.object, k)] for k in self.fields)


class CustomerSerializer(BraintreeSerializer):
    fields = ['id', 'created_at', 'updated_at']
