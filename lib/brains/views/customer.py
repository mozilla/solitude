from rest_framework.decorators import api_view
from rest_framework.response import Response

from lib.brains import serializers
from lib.brains.client import get_client
from lib.brains.errors import BraintreeResultError
from lib.brains.forms import BuyerForm
from lib.brains.models import BraintreeBuyer
from solitude.logger import getLogger

log = getLogger('s.brains')


@api_view(['POST'])
def create(request):
    client = get_client().Customer
    form = BuyerForm(request.DATA)

    if not form.is_valid():
        return Response(form.errors, status=400)

    result = client.create()
    if not result.is_success:
        log.warning('Error on creating Customer: {0}, {1}'
                    .format(form.cleaned_data['uuid'], result.message))
        raise BraintreeResultError(result)

    log.info('Braintree customer created: {0}'.format(result.customer.id))

    braintree_buyer = BraintreeBuyer.objects.create(
        buyer=form.buyer, braintree_id=result.customer.id)

    log.info('Braintree buyer created: {0}'.format(braintree_buyer.pk))

    res = serializers.Namespaced(
        serializers.LocalBuyer(instance=braintree_buyer),
        serializers.Customer(instance=result.customer)
    )
    return Response(res.data, status=201)
