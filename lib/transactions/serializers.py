import uuid

from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.transactions.models import Transaction
from solitude.base import BaseSerializer
from solitude.related_fields import PathRelatedField


class TransactionSerializer(BaseSerializer):
    buyer = PathRelatedField(view_name='generic:buyer-detail', required=False)
    seller = PathRelatedField(view_name='generic:seller-detail',
                              required=False)
    seller_product = PathRelatedField(
        view_name='generic:sellerproduct-detail', required=False)
    related = PathRelatedField(
        view_name='generic:transaction-detail', required=False)
    uuid = serializers.CharField(required=False)

    class Meta:
        model = Transaction
        fields = [
            'amount', 'buyer', 'carrier', 'created', 'currency', 'notes',
            'pay_url', 'provider', 'region', 'related', 'relations',
            'resource_pk', 'resource_uri', 'seller',
            'seller_product', 'source', 'status', 'status_reason', 'type',
            'uid_pay', 'uid_support', 'uuid'
        ]

    def transform_relations(self, obj, value):
        objs = []
        if obj:
            relations = Transaction.objects.filter(related=obj)
            for relation in relations:
                # Note that if this relation has more relations, it will fail
                # to serialize on the recursiveness. This can be fixed in
                # DRF 3.x with recursivefield (if we want to).
                objs.append(TransactionSerializer(relation).data)

        return objs

    def resource_uri(self, pk):
        return reverse('generic:transaction-detail', kwargs={'pk': pk})

    def validate_uuid(self, attrs, source):
        # Provide a default uuid.
        if not attrs.get('uuid') and not self.object:
            attrs['uuid'] = 'solitude:' + str(uuid.uuid4())
        return attrs
