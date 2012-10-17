from solitude.base import ModelResource
from tastypie import fields

from .forms import BuyerFormValidation, BuyerValidation
from .models import Buyer, BuyerPaypal


class BuyerResource(ModelResource):
    paypal = fields.ToOneField('lib.buyers.resources.BuyerPaypalResource',
                               'paypal', blank=True, full=True,
                               null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Buyer.objects.all()
        fields = ['uuid', 'pin']
        list_allowed_methods = ['post', 'get', 'put']
        allowed_methods = ['get', 'put']
        resource_name = 'buyer'
        validation = BuyerFormValidation(form_class=BuyerValidation)
        filtering = {
            'uuid': 'exact',
        }

    def build_bundle(self, obj=None, data=None, request=None):
        if obj is None and (data is not None and (data.get('pk') or
                                                  data.get('id'))):
            pk = data.get('pk', data.get('id'))
            obj = Buyer.objects.get(pk=pk)
        return super(BuyerResource, self).build_bundle(obj, data, request)


class BuyerPaypalResource(ModelResource):
    buyer = fields.ToOneField('lib.buyers.resources.BuyerResource',
                              'buyer')
    key = fields.BooleanField(attribute='key_exists')

    class Meta(ModelResource.Meta):
        queryset = BuyerPaypal.objects.all()
        fields = ['buyer', 'currency', 'expiry', 'key']
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'delete', 'patch']
        resource_name = 'buyer'
