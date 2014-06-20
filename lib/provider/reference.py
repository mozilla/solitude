from lib.provider.serializers import (SellerProductReferenceSerializer,
                                      SellerReferenceSerializer)
from lib.sellers.models import SellerProductReference, SellerReference

from solitude.base import NonDeleteModelViewSet
from solitude.logger import getLogger

log = getLogger('s.provider')


class SellerReferenceView(NonDeleteModelViewSet):
    model = SellerReference
    serializer_class = SellerReferenceSerializer


class SellerProductReferenceView(NonDeleteModelViewSet):
    model = SellerProductReference
    serializer_class = SellerProductReferenceSerializer
