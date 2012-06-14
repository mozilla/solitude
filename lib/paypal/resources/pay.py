from cached import Resource

from lib.paypal.client import Client
from lib.paypal.forms import (CheckPurchaseValidation, PayValidation,
                              RefundValidation)
from lib.paypal.signals import create


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
        create.send(sender=self, bundle=bundle, form=form.cleaned_data)
        return bundle


class CheckPurchaseResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'pay-check'
        list_allowed_methods = ['post']
        form = CheckPurchaseValidation
        method = 'check_purchase'


class RefundResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'refund'
        list_allowed_methods = ['post']
        form = RefundValidation
        method = 'get_refund'
