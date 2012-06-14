from solitude.base import ModelResource
from tastypie import fields
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
        list_allowed_methods = ['post']
        allowed_methods = ['get']
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerValidation)


class SellerPaypalResource(ModelResource):
    seller = fields.ToOneField('lib.sellers.resources.SellerResource',
                              'seller')

    class Meta(ModelResource.Meta):
        queryset = SellerPaypal.objects.all()
        fields = ['paypal_id', 'seller']
        list_allowed_methods = ['post']
        allowed_methods = ['get', 'put']
        resource_name = 'seller'
        validation = FormValidation(form_class=SellerPaypalValidation)

    def dehydrate(self, bundle):
        # Never disclose the paypal tokens, just disclose their presence.
        bundle.data['token'] = bool(bundle.obj.token)
        bundle.data['secret'] = bool(bundle.obj.secret)
        return bundle.data
