from cached import Resource

from lib.paypal.client import Client
from lib.paypal.forms import (CheckPurchaseValidation, PayValidation,
                              RefundValidation)
from lib.paypal.signals import create
from lib.transactions.models import PaypalTransaction


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
        method = 'check_purchase'

    def obj_create(self, bundle, request, **kwargs):
        form = CheckPurchaseValidation(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        # Allow lookup by either pay_key or uuid.
        pay_key = form.cleaned_data.get('pay_key', '')
        if not pay_key:
            uuid = self.get_object_or_404(PaypalTransaction,
                                          uuid=form.cleaned_data['uuid'])
            pay_key = uuid.pay_key

        paypal = Client()
        bundle.data = getattr(paypal, self._meta.method)(pay_key)
        create.send(sender=self, bundle=bundle)
        return bundle


class RefundResource(Resource):

    class Meta(Resource.Meta):
        resource_name = 'refund'
        list_allowed_methods = ['post']
        form = RefundValidation
        method = 'get_refund'
