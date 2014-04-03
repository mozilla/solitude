from .serializers import SellerBokuSerializer

from lib.sellers.models import SellerBoku

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied


class SellerBokuViewSet(viewsets.ModelViewSet):
    model = SellerBoku
    serializer_class = SellerBokuSerializer

    def destroy(self, request, pk=None):
        raise PermissionDenied
