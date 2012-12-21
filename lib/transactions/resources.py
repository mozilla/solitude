import uuid

from django.conf.urls.defaults import url

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
                  'uid_pay', 'uid_support', 'type', 'status', 'related',
                  'notes']
        list_allowed_methods = ['get', 'post']
        allowed_methods = ['get', 'patch']
        resource_name = 'transaction'
        filtering = {
            'uuid': 'exact',
            'seller': 'exact',
            'provider': 'exact'
        }

    def override_urls(self):
         return [
            url(r"^(?P<resource_name>transaction)/(?P<uuid>.*)/$",
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
         ]

    prepend_urls = override_urls

    def hydrate_uuid(self, bundle):
        bundle.data.setdefault('uuid', str(uuid.uuid4()))
        return bundle
