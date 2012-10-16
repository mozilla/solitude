from solitude.base import ModelResource
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.validation import FormValidation

from .forms import (SellerValidation, SellerProductValidation,
                    SellerBlueviaValidation, SellerPaypalValidation)
from .models import Seller, SellerProduct, SellerBluevia, SellerPaypal


class SellerResource(ModelResource):
    paypal = fields.ToOneField('lib.sellers.resources.SellerPaypalResource',
                               'paypal', blank=True, full=True,
                               null=True, readonly=True)
    bluevia = fields.ToOneField('lib.sellers.resources.SellerBlueviaResource',
                                'bluevia', blank=True, full=True,
                                null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Seller.objects.all()
        fields = ('uuid',)
        list_allowed_methods = ('post', 'get')
        allowed_methods = ('get',)
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


class SellerBlueviaResource(ModelResource):
    seller = fields.ToOneField('lib.sellers.resources.SellerResource',
                               'seller')

    class Meta(ModelResource.Meta):
        queryset = SellerBluevia.objects.all()
        excludes = ['id']
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'put', 'patch']
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerBlueviaValidation)


class SellerProductResource(ModelResource):
    seller = fields.ToOneField('lib.sellers.resources.SellerResource',
                               'seller')

    class Meta(ModelResource.Meta):
        excludes = ['id']
        queryset = SellerProduct.objects.all()
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'put', 'patch']
        resource_name = 'product'
        validation = FormValidation(form_class=SellerProductValidation)
