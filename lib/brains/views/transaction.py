from rest_framework.response import Response

from lib.brains.models import BraintreeTransaction
from lib.brains.serializers import LocalTransaction
from solitude.base import NonDeleteModelViewSet


class TransactionViewSet(NonDeleteModelViewSet):
    queryset = BraintreeTransaction.objects.all()
    serializer_class = LocalTransaction

    def create(self, *args, **kw):
        # Transactions will be created via the Braintree webhook.
        return Response(status=405)

    def update(self, *args, **kw):
        # Not sure what a patch to this object would do.
        return Response(status=405)
