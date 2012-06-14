from cached import Resource

from lib.paypal.client import Client
from lib.paypal.forms import CheckPurchaseValidation, PayValidation


class PayResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'pay'
        list_allowed_methods = ['post']

    def obj_create(self, bundle, request, **kwargs):
        form = PayValidation(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        paypal = Client()
        # TODO: there might be a lot more we can do here.
        bundle.data = paypal.get_pay_key(*form.args(), **form.kwargs())
        return bundle


class CheckPurchaseResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'pay-check'
        list_allowed_methods = ['post']
        form = CheckPurchaseValidation
        method = 'check_purchase'
