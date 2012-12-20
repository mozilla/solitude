import uuid

from tastypie import fields

from lib.transactions.models import Transaction
from solitude.base import ModelResource


class TransactionResource(ModelResource):
    seller_product = fields.ToOneField(
                'lib.sellers.resources.SellerProductResource',
                'seller_product', blank=True, full=False, null=True)
    related = fields.ToOneField(
                'lib.transactions.resources.TransactionResource',
                'related', blank=True, full=False, null=True)

    class Meta(ModelResource.Meta):
        queryset = Transaction.objects.filter()
        fields = ['uuid', 'seller_product', 'amount', 'currency', 'provider',
                  'uid_support', 'type', 'status', 'related']
        list_allowed_methods = ['get', 'post']
        allowed_methods = ['get']
        resource_name = 'transaction'
        filtering = {
            'uuid': 'exact',
            'seller': 'exact',
            'provider': 'exact'
        }

    def hydrate_uuid(self, bundle):
        bundle.data.setdefault('uuid', str(uuid.uuid4()))
        return bundle
