from rest_framework.response import Response

from lib.bango.errors import ProcessError
from lib.bango.forms import CreateBangoNumberForm
from lib.bango.serializers import SellerProductBangoSerializer
from lib.bango.views.base import BangoResource
from lib.sellers.models import SellerProductBango
from solitude.base import NonDeleteModelViewSet


class ProductViewSet(NonDeleteModelViewSet, BangoResource):
    queryset = SellerProductBango.objects.filter()
    serializer_class = SellerProductBangoSerializer
    filter_fields = ('seller_product__seller', 'seller_product__external_id')

    def create(self, request, *args, **kw):
        try:
            serial, form = self.process(
                serial_class=SellerProductBangoSerializer,
                form_class=CreateBangoNumberForm,
                request=request)
        except ProcessError, exc:
            return exc.response

        data = form.cleaned_data
        data['packageId'] = serial.object.seller_bango.package_id

        resp = self.client('CreateBangoNumber', data)

        product = SellerProductBango.objects.create(
            seller_bango=serial.object.seller_bango,
            seller_product=serial.object.seller_product,
            bango_id=resp.bango,
        )

        serializer = SellerProductBangoSerializer(product)
        return Response(serializer.data, status=201)
