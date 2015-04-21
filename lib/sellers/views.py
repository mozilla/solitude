from lib.sellers.models import Seller, SellerProduct
from lib.sellers.serializers import SellerProductSerializer, SellerSerializer
from solitude.base import NonDeleteModelViewSet


class SellerViewSet(NonDeleteModelViewSet):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    filter_fields = ('uuid', 'active')


class SellerProductViewSet(NonDeleteModelViewSet):
    queryset = SellerProduct.objects.all()
    serializer_class = SellerProductSerializer
    filter_fields = (
        'external_id', 'public_id', 'seller__uuid', 'seller__active'
    )
