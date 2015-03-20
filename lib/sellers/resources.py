from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.validation import FormValidation

from solitude.base import ModelResource, ModelFormValidation
from .forms import SellerValidation, SellerProductValidation
from .models import Seller, SellerProduct


class SellerResource(ModelResource):
    bango = fields.ToOneField('lib.bango.resources.package.PackageResource',
                              'bango', blank=True, full=True,
                              null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Seller.objects.filter()
        fields = ('uuid', 'active')
        list_allowed_methods = ('post', 'get')
        allowed_methods = ('get',)
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerValidation)
        filtering = {
            'uuid': 'exact',
            'active': 'exact',
        }


class SellerProductResource(ModelResource):
    seller = fields.ForeignKey('lib.sellers.resources.SellerResource',
                               'seller')

    class Meta(ModelResource.Meta):
        excludes = ['id']
        queryset = SellerProduct.objects.filter()
        list_allowed_methods = ['post', 'get']
        allowed_methods = ['get', 'put', 'patch']
        resource_name = 'product'
        validation = ModelFormValidation(form_class=SellerProductValidation)
        filtering = {
            'external_id': 'exact',
            'public_id': 'exact',
            'seller': ALL_WITH_RELATIONS,
        }

    def dehydrate(self, bundle):
        bundle.data['resource_pk'] = bundle.obj.pk
        bundle.data['seller_uuids'] = bundle.obj.supported_providers()
        return bundle
