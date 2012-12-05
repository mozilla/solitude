from django.core.urlresolvers import resolve

from solitude.base import get_object_or_404, ModelResource, Resource
from tastypie import fields
from tastypie.validation import FormValidation

from .forms import BuyerForm, BuyerFormValidation, BuyerVerifyPinForm
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

    def is_valid(self, bundle, request):
        # Tastypie will check is_valid on the object by validating the form,
        # but on PUTes and PATCHes it does so without instantiating the object.
        # Without the object on the model.instance, the uuid check does not
        # exclude the original object being changed and so the validation
        # will fail. This patch will force the object to be added before
        # validation,
        #
        # There are two ways to spot when we should be doing this:
        # 1. When there is a specific resource_pk in the PUT or PATCH.
        # 2. When the request.path resolves to having a pk in it.
        # If either of those match, get_via_uri will do the right thing.
        if 'resource_uri' in bundle.data or 'pk' in resolve(request.path)[2]:
            try:
                bundle.obj = self.get_via_uri(request.path)
            except Buyer.DoesNotExist:
                pass
        return super(BuyerResource, self).is_valid(bundle, request)


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


class BuyerVerifyPin(object):
    pk = 'verify_pin'
    uuid = 'fake'
    valid = False


class BuyerVerifyPinResource(Resource):
    uuid = fields.CharField(attribute='uuid')
    valid = fields.BooleanField(attribute='valid')

    class Meta(Resource.Meta):
        allowed_methods = ('post')
        resource_name = 'verify_pin'
        object_class = BuyerVerifyPin
        validation = FormValidation(form_class=BuyerVerifyPinForm)

    def obj_create(self, bundle, request=None, **kwargs):
        bundle.obj = BuyerVerifyPin()
        buyer = get_object_or_404(Buyer, uuid=bundle.data['uuid'])
        bundle.obj.uuid = bundle.data['uuid']
        bundle.obj.valid = buyer.pin == bundle.data.pop('pin')
        return bundle

    def get_resource_uri(self, bundle_or_obj):
        # Needed as this isn't a model resource.
        return 'no_uri'
