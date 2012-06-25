from cached import Resource

from lib.paypal.ipn import IPN
from lib.paypal.forms import IPNForm

class IPNResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'ipn'
        list_allowed_methods = ['post']
        allowed_methods = []

    def obj_create(self, bundle, request, **kwargs):
        form = IPNForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        ipn = IPN(form.cleaned_data['data'])
        ipn.process()
        bundle.ipn = ipn
        return bundle

    def dehydrate(self, bundle):
        bundle.data['status'] = bundle.ipn.status
        if bundle.data['status'] != 'IGNORED':
            bundle.data['uuid'] = bundle.ipn.transaction['tracking_id']
            bundle.data['action'] = bundle.ipn.action
        return bundle
