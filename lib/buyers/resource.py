import uuid

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from solitude.base import Resource, ModelResource
from tastypie import fields, http
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.validation import FormValidation

from .forms import BuyerValidation, PreapprovalValidation
from .models import Buyer, BuyerPaypal
from lib.paypal.client import Client


class BuyerResource(ModelResource):
    paypal = fields.ToOneField('lib.buyers.resource.BuyerPaypalResource',
                               'paypal', blank=True, full=True,
                               null=True, readonly=True)

    class Meta(ModelResource.Meta):
        queryset = Buyer.objects.all()
        fields = ['uuid']
        list_allowed_methods = ['post']
        allowed_methods = ['get']
        resource_name = 'buyer'
        validation = FormValidation(form_class=BuyerValidation)


class Blank(object):
    pass


# TODO: if we use this pattern a lot and we just might, this needs extracting
# into a common class.
class PreapprovalResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'preapproval'
        object_class = Blank
        list_allowed_methods = ['post']
        allowed_methods = ['put', 'get', 'delete']

    def get_resource_uri(self, bundle):
        return reverse('api_dispatch_detail',
                        kwargs={'api_name': 'paypal',
                                'resource_name': self._meta.resource_name,
                                'pk': str(self.uuid)})

    def obj_create(self, bundle, request, **kwargs):
        form = PreapprovalValidation(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = Client()
        args = [form.cleaned_data.get(k) for k in
                ('start', 'end', 'return_url', 'cancel_url')]
        bundle.data = {'key': paypal.get_preapproval_key(*args)['key'],
                       'uuid': form.cleaned_data['uuid'].uuid}
        self.uuid = uuid.uuid4()
        cache.set('preapproval:%s' % self.uuid, bundle.data)
        return bundle

    def put_detail(self, request, **kwargs):
        return super(PreapprovalResource, self).put_detail(request, **kwargs)

    def obj_update(self, bundle, request, **kwargs):
        self.uuid = kwargs['pk']
        data = cache.get('preapproval:%s' % self.uuid)
        if not data:
            raise ImmediateHttpResponse(response=http.HttpNotFound())

        paypal = self.get_object_or_404(BuyerPaypal,
                                        buyer__uuid=data.get('uuid'))
        paypal.key = data['key']
        paypal.save()
        return bundle

    def obj_get(self, request, **kwargs):
        assert kwargs.get('pk')  # Prevent empty pk.
        self.uuid = kwargs['pk']
        return cache.get('preapproval:%s' % self.uuid)

    def obj_delete(self, request, **kwargs):
        assert kwargs.get('pk')  # Prevent empty pk.
        self.uuid = kwargs['pk']
        cache.delete('preapproval:%s' % self.uuid)

    def dehydrate(self, bundle):
        bundle.data['pk'] = self.uuid
        return bundle.data


class BuyerPaypalResource(ModelResource):
    buyer = fields.ToOneField('lib.buyers.resource.BuyerResource',
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
        return bundle.data
