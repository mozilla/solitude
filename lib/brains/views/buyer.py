from lib.brains.models import BraintreeBuyer
from lib.brains.serializers import LocalBuyer
from solitude.base import NoAddModelViewSet


class BraintreeBuyerViewSet(NoAddModelViewSet):
    queryset = BraintreeBuyer.objects.all()
    serializer_class = LocalBuyer
    filter_fields = ('buyer', 'active')
