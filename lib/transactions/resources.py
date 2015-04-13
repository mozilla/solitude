import uuid

from tastypie import fields

from .forms import UpdateForm
from lib.transactions.models import Transaction
from solitude.base import ModelResource


class TransactionResource(ModelResource):
    buyer = fields.ToOneField(
        'lib.buyers.resources.BuyerResource',
        'buyer', blank=True, full=False, null=True)
    seller = fields.ToOneField(
        'lib.sellers.resources.SellerResource',
        'seller', blank=True, full=False, null=True)
    seller_product = fields.ToOneField(
        'lib.sellers.resources.SellerProductResource',
        'seller_product', blank=True, full=False, null=True)
    related = fields.ToOneField(
        'lib.transactions.resources.TransactionResource',
        'related', blank=True, full=False, null=True, readonly=True)
    relations = fields.ToManyField(
        'lib.transactions.resources.TransactionResource',
        lambda bundle: Transaction.objects.filter(related=bundle.obj),
        blank=True, full=True, null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Transaction.objects.filter()
        fields = ['uuid', 'seller_product', 'amount', 'currency',
                  'pay_url', 'provider', 'uid_pay', 'uid_support',
                  'type', 'status', 'status_reason', 'related', 'notes',
                  'created', 'buyer', 'source', 'carrier', 'region']
        list_allowed_methods = ['get', 'post']
        allowed_methods = ['get', 'patch']
        resource_name = 'transaction'
        filtering = {
            'uuid': 'exact',
            'seller': 'exact',
            'provider': 'exact'
        }

    def update_in_place(self, request, original_data, new_data):
        form = UpdateForm(new_data, original_data=original_data.data,
                          request=request)
        if form.is_valid():
            return (super(TransactionResource, self)
                    .update_in_place(request, original_data, new_data))
        raise self.form_errors(form)

    def hydrate_uuid(self, bundle):
        bundle.data.setdefault('uuid', str(uuid.uuid4()))
        return bundle
