from tastypie import fields
from tastypie.validation import FormValidation

from solitude.base import get_object_or_404, log_cef, ModelResource, Resource

from .forms import BuyerForm, BuyerFormValidation, PinForm
from .models import Buyer


class BuyerResource(ModelResource):
    pin_failures = fields.IntegerField(attribute='pin_failures', readonly=True)
    pin_is_locked_out = fields.BooleanField(attribute='locked_out',
                                            blank=True, null=True,
                                            readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Buyer.objects.filter()
        fields = ['uuid', 'pin', 'active', 'new_pin', 'needs_pin_reset',
                  'email', 'pin_confirmed', 'pin_was_locked_out']
        list_allowed_methods = ['get', 'post']
        allowed_methods = ['get', 'patch', 'put']
        resource_name = 'buyer'
        validation = BuyerFormValidation(form_class=BuyerForm)
        filtering = {
            'uuid': 'exact',
            'active': 'exact',
        }

    def dehydrate_pin(self, bundle):
        return bool(bundle.obj.pin)

    def dehydrate_new_pin(self, bundle):
        return bool(bundle.obj.new_pin)


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
    valid = fields.BooleanField(attribute='valid', default=False)
    locked = fields.BooleanField(attribute='locked', default=False)

    class Meta(BuyerEndpointBase.Meta):
        resource_name = 'verify_pin'

    def obj_create(self, bundle, request=None, **kwargs):
        buyer = self.get_data(bundle)
        if buyer.pin_confirmed:
            if buyer.locked_out:
                log_cef('Attempted access to locked out account: %s'
                        % buyer.uuid, request, severity=1)
                bundle.obj.locked = True
                return bundle
            bundle.obj.valid = buyer.pin == bundle.data.pop('pin')
            if not bundle.obj.valid:
                locked = buyer.incr_lockout()
                if locked:
                    bundle.obj.locked = True
                    log_cef('Locked out account: %s' % buyer.uuid,
                            request, severity=1)
            if bundle.obj.valid:
                buyer.clear_lockout(clear_was_locked=True)
        else:
            bundle.obj.valid = False
        return bundle


class BuyerResetPinResource(BuyerEndpointBase):
    confirmed = fields.BooleanField(attribute='confirmed')

    class Meta(BuyerEndpointBase.Meta):
        resource_name = 'reset_confirm_pin'

    def obj_create(self, bundle, request=None, **kwargs):
        buyer = self.get_data(bundle)
        pin = bundle.data.pop('pin')
        if buyer.locked_out:
            log_cef('Attempted access to locked out account: %s'
                    % buyer.uuid, request, severity=1)
            bundle.obj.confirmed = False
            return bundle
        if buyer.new_pin == pin:
            buyer.pin = pin
            buyer.new_pin = None
            buyer.needs_pin_reset = False
            buyer.pin_confirmed = True
            buyer.pin_was_locked_out = False
            buyer.save()
            bundle.obj.confirmed = True
        else:
            bundle.obj.confirmed = False
        return bundle
