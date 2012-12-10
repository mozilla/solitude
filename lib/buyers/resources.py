from solitude.base import get_object_or_404, ModelResource, Resource
from tastypie import fields
from tastypie.validation import FormValidation

from .forms import BuyerForm, BuyerFormValidation, PinForm
from .models import Buyer, BuyerPaypal


class BuyerResource(ModelResource):
    paypal = fields.ToOneField('lib.buyers.resources.BuyerPaypalResource',
                               'paypal', blank=True, full=True,
                               null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Buyer.objects.all()
        fields = ['uuid', 'pin']
        list_allowed_methods = ['get', 'post', 'put']
        allowed_methods = ['get', 'patch', 'put']
        resource_name = 'buyer'
        validation = BuyerFormValidation(form_class=BuyerForm)
        filtering = {
            'uuid': 'exact',
        }

    def dehydrate_pin(self, bundle):
        return bool(bundle.obj.pin)


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


class BuyerFakeObject(object):
    pk = ''
    uuid = 'fake'


class BuyerEndpointBase(Resource):
    uuid = fields.CharField(attribute='uuid')

    class Meta(Resource.Meta):
        allowed_methods = ('post')
        object_class = BuyerFakeObject
        validation = FormValidation(form_class=PinForm)

    def get_data(self, bundle):
        bundle.obj = self.Meta.object_class()
        bundle.obj.pk = self.Meta.resource_name
        bundle.obj.uuid = bundle.data['uuid']
        return get_object_or_404(Buyer, uuid=bundle.data['uuid'])

    def get_resource_uri(self, bundle_or_obj):
        return 'no_uri'


class BuyerConfirmPinResource(BuyerEndpointBase):
    confirmed = fields.BooleanField(attribute='confirmed')

    class Meta(BuyerEndpointBase.Meta):
        resource_name = 'confirm_pin'

    def obj_create(self, bundle, request=None, **kwargs):
        buyer = self.get_data(bundle)
        if buyer.pin == bundle.data.pop('pin'):
            buyer.pin_confirmed = True
            buyer.save()
            bundle.obj.confirmed = True
        else:
            bundle.obj.confirmed = False
        return bundle


class BuyerVerifyPinResource(BuyerEndpointBase):
    valid = fields.BooleanField(attribute='valid')

    class Meta(BuyerEndpointBase.Meta):
        resource_name = 'verify_pin'

    def obj_create(self, bundle, request=None, **kwargs):
        buyer = self.get_data(bundle)
        if buyer.pin_confirmed:
            bundle.obj.valid = buyer.pin == bundle.data.pop('pin')
        else:
            bundle.obj.valid = False
        return bundle
