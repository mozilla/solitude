from rest_framework.response import Response

from lib.brains.models import BraintreeBuyer
from lib.brains.serializers import BraintreeBuyerSerializer
from solitude.base import NonDeleteModelViewSet


class BraintreeBuyerViewSet(NonDeleteModelViewSet):
    queryset = BraintreeBuyer.objects.all()
    serializer_class = BraintreeBuyerSerializer
    filter_fields = ('buyer', 'active')

    def create(self, *args, **kw):
        # You must create a braintreebuyer through the customer API to ensure
        # that the braintree customer and solitude buyer are all created.
        return Response('Call braintree customer create', status=405)
