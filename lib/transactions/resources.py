from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS

from lib.transactions.models import Transaction
from solitude.base import ModelResource


class TransactionResource(ModelResource):
    seller = fields.ToOneField('lib.sellers.resources.SellerPaypalResource',
                'seller', blank=True, full=False, null=True, readonly=True)
    related = fields.ToOneField(
                'lib.transactions.resources.TransactionResource',
                'related', blank=True, full=False, null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Transaction.objects.all()
        fields = ['uuid', 'seller', 'amount', 'currency', 'provider',
                  'uid_support', 'type', 'status', 'related']
        list_allowed_methods = ['get']
        allowed_methods = ['get']
        resource_name = 'transaction'
        filtering = {
            'uuid': 'exact',
            'seller': 'exact',
            'provider': 'exact'
        }
