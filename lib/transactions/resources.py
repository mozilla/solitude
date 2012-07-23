from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS

from lib.transactions.models import PaypalTransaction
from solitude.base import ModelResource


class TransactionResource(ModelResource):
    seller = fields.ToOneField('lib.sellers.resources.SellerPaypalResource',
                'seller', blank=True, full=False, null=True, readonly=True)
    related = fields.ToOneField(
                'lib.transactions.resources.TransactionResource',
                'related', blank=True, full=False, null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = PaypalTransaction.objects.all()
        fields = ['uuid', 'seller', 'amount', 'currency', 'correlation_id',
                  'type', 'status', 'related']
        list_allowed_methods = ['get']
        allowed_methods = ['get']
        resource_name = 'transaction'
        filtering = {
            'uuid': 'exact',
            'seller': ALL_WITH_RELATIONS,
        }
