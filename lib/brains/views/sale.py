from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.brains.client import get_client
from lib.brains.errors import BraintreeResultError
from lib.brains.forms import SaleForm
from lib.brains.models import BraintreeTransaction
from lib.brains.serializers import LocalTransaction, Namespaced
from lib.transactions import constants
from lib.transactions.models import Transaction
from lib.transactions.serializers import TransactionSerializer
from solitude.errors import FormError
from solitude.logger import getLogger

log = getLogger('s.brains')


@api_view(['POST'])
def create(request):
    client = get_client().Transaction
    form = SaleForm(request.DATA)

    if not form.is_valid():
        raise FormError(form.errors)

    result = client.sale(form.braintree_data)
    if not result.is_success:
        log.warning('Error on one-off sale: {}'.format(form.braintree_data))
        raise BraintreeResultError(result)

    our_transaction = Transaction.objects.create(
        amount=result.transaction.amount,
        buyer=form.buyer,
        currency=result.transaction.currency_iso_code,
        provider=constants.PROVIDER_BRAINTREE,
        seller=form.seller_product.seller,
        seller_product=form.seller_product,
        status=constants.STATUS_CHECKED,
        type=constants.TYPE_PAYMENT,
        uid_support=result.transaction.id
    )
    our_transaction.uuid = our_transaction.create_short_uid()
    our_transaction.save()
    log.info('Transaction created: {}'.format(our_transaction.pk))

    braintree_transaction = BraintreeTransaction.objects.create(
        kind='submit_for_settlement',
        paymethod=form.cleaned_data['paymethod'],
        transaction=our_transaction,

    )
    log.info('BraintreeTransaction created: {}'
             .format(braintree_transaction.pk))

    res = Namespaced(
        braintree={},  # Not sure if there's anything useful to add here.
        mozilla={
            'braintree': LocalTransaction(braintree_transaction),
            'generic': TransactionSerializer(our_transaction)
        }
    )
    return Response(res.data, status=200)
