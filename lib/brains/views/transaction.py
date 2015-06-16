from rest_framework.response import Response

from lib.brains.models import BraintreeTransaction
from lib.brains.serializers import LocalTransaction
from solitude.base import NoAddModelViewSet


class TransactionViewSet(NoAddModelViewSet):
    queryset = BraintreeTransaction.objects.all()
    serializer_class = LocalTransaction

    def update(self, *args, **kw):
        # Not sure what a patch to this object would do.
        return Response(status=405)
