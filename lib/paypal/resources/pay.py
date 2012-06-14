from cached import Resource

from lib.paypal.client import Client
from lib.paypal.forms import PayValidation


class PayResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'pay'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = PayValidation(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = Client()
        bundle.data = paypal.get_pay_key(*form.args(), **form.kwargs())
        return bundle
