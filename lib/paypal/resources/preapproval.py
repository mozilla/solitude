from cached import Resource

from lib.buyers.models import BuyerPaypal
from lib.paypal.client import Client
from lib.paypal.forms import PreapprovalValidation
from lib.paypal.urls import urls


class PreapprovalResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'preapproval'
        list_allowed_methods = ['post']
        allowed_methods = ['put', 'get', 'delete']

    def obj_create(self, bundle, request, **kwargs):
        form = PreapprovalValidation(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = Client()
        bundle.data = {'key': paypal.get_preapproval_key(*form.args())['key'],
                       'uuid': form.cleaned_data['uuid'].uuid}
        bundle.obj = self.obj()
        bundle.obj.set(bundle.data)
        return bundle

    def obj_update(self, bundle, request, **kwargs):
        self.uuid = kwargs['pk']
        data = self.obj(self.uuid).get_or_404()
        paypal = self.get_object_or_404(BuyerPaypal,
                                        buyer__uuid=data.get('uuid'))
        paypal.key = data['key']
        paypal.save()
        return bundle

    def obj_get(self, request, **kwargs):
        assert kwargs.get('pk')  # Prevent empty pk.
        return self.obj(kwargs.get('pk'))

    def obj_delete(self, request, **kwargs):
        assert kwargs.get('pk')  # Prevent empty pk.
        self.obj(kwargs.get('pk')).delete()

    def dehydrate(self, bundle):
        bundle.data['pk'] = bundle.obj.pk
        if 'key' in bundle.data:
            bundle.data['paypal_url'] = (urls['grant-preapproval'] +
                                         bundle.data['key'])
        return bundle.data
