from solitude.base import ModelResource
from tastypie import fields
from tastypie.validation import FormValidation

from .forms import BuyerValidation
from .models import Buyer, BuyerPaypal


class BuyerResource(ModelResource):
    paypal = fields.ToOneField('lib.buyers.resources.BuyerPaypalResource',
                               'paypal', blank=True, full=True,
                               null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Buyer.objects.all()
        fields = ['uuid']
        list_allowed_methods = ['post']
        allowed_methods = ['get']
        resource_name = 'buyer'
        validation = FormValidation(form_class=BuyerValidation)


class BuyerPaypalResource(ModelResource):
    buyer = fields.ToOneField('lib.buyers.resources.BuyerResource',
                              'buyer')

    class Meta(ModelResource.Meta):
        queryset = BuyerPaypal.objects.all()
        fields = ['buyer', 'currency', 'expiry']
        list_allowed_methods = ['post']
        allowed_methods = ['get']
        resource_name = 'buyer'

    def dehydrate(self, bundle):
        # Never disclose the paypal key, just disclose it's presence.
        bundle.data['key'] = bool(bundle.obj.key)
        return super(BuyerPaypalResource, self).dehydrate(bundle)
