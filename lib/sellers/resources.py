from solitude.base import ModelResource
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.validation import FormValidation

from .forms import SellerValidation, SellerPaypalValidation
from .models import Seller, SellerPaypal


class SellerResource(ModelResource):
    paypal = fields.ToOneField('lib.sellers.resources.SellerPaypalResource',
                               'paypal', blank=True, full=True,
                               null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Seller.objects.all()
        fields = ['uuid']
        list_allowed_methods = ['post', 'get']
        allowed_methods = ['get']
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerValidation)
        filtering = {
            'uuid': 'exact',
        }


class SellerPaypalResource(ModelResource):
    seller = fields.ToOneField('lib.sellers.resources.SellerResource',
                               'seller')
    secret = fields.BooleanField(readonly=True, attribute='secret_exists')
    token = fields.BooleanField(readonly=True, attribute='token_exists')

    class Meta(ModelResource.Meta):
        queryset = SellerPaypal.objects.all()
        excludes = ['id']
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'put', 'patch']
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerPaypalValidation)
        filtering = {
            'seller': ALL_WITH_RELATIONS,
        }
