import uuid

from lib.bango.client import get_client
from lib.bango.forms import RefundForm
from lib.transactions.constants import STATUS_COMPLETED, TYPE_REFUND
from lib.transactions.models import Transaction
from solitude.base import ModelResource


class RefundResource(ModelResource):
    """
    A specific resource for creating refunds and then checking the state of
    that refund against Bango. Since a transaction is created, you can examine
    the state of the transaction in solitude without having to check against
    Bango.
    """

    class Meta(ModelResource.Meta):
        queryset = Transaction.objects.filter()
        list_allowed_methods = ['post']
        resource_name = 'refund'

    def obj_create(self, bundle, request, **kw):
        form = RefundForm(bundle.data)
        if not form.is_valid():
            raise self.form_errors(form)

        obj = form.cleaned_data['uuid']

        external_uuid = str(uuid.uuid4())
        res = get_client().DoRefund({
            'transactionId': obj.uid_support,
            'refundType': 'OPERATOR',
            'externalTransactionId': external_uuid
        })

        # If that succeeded, create a new transaction for the refund.
        obj = Transaction.objects.create(
            amount=obj.amount,
            buyer=obj.buyer,
            currency=obj.currency,
            provider=obj.provider,
            related=obj,
            seller_product=obj.seller_product,
            # Note: check on this when we can actually do refunds, but for
            # the moment we'll assume they go straight through.
            status=STATUS_COMPLETED,
            source='',
            type=TYPE_REFUND,
            uid_pay=res.refundTransactionId)

        # Turn the object back into a bundle so that we get the new transaction
        # in the response.
        bundle.obj = obj
        return bundle
