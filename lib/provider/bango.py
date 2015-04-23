from rest_framework.response import Response

from lib.bango.forms import (CreateBangoNumberForm, MakePremiumForm,
                             UpdateRatingForm)
from lib.bango.serializers import SellerProductBangoSerializer
from lib.bango.views.base import BangoResource
from lib.sellers.models import SellerProductBango
from solitude.base import BaseAPIView


class ProductView(BaseAPIView):

    """
    Override creating a product.
    """

    def post(self, request, *args, **kwargs):
        view = BangoResource()
        form = CreateBangoNumberForm(request.DATA)
        if not form.is_valid():
            return self.form_errors(form)

        serial = SellerProductBangoSerializer(data=request.DATA)
        if not serial.is_valid():
            return Response(serial.errors, status=400)

        # Create the product.
        data = form.cleaned_data
        data['packageId'] = serial.object.seller_bango.package_id

        resp = view.client('CreateBangoNumber', data)

        product = SellerProductBango.objects.create(
            seller_bango=serial.object.seller_bango,
            seller_product=serial.object.seller_product,
            bango_id=resp.bango,
        )

        # Make it premium.
        data = request.DATA.copy()
        data['bango'] = resp.bango
        data['price'] = '0.99'
        data['currencyIso'] = 'USD'

        form = MakePremiumForm(data)
        if not form.is_valid():
            return self.form_errors(form)

        data = form.cleaned_data
        data['bango'] = resp.bango
        view.client('MakePremiumPerAccess', data)

        for rating, scheme in (['UNIVERSAL', 'GLOBAL'],
                               ['GENERAL', 'USA']):
            # Make it global and US rating.
            data.update({'rating': rating, 'ratingScheme': scheme})
            form = UpdateRatingForm(data)
            if not form.is_valid():
                return self.form_errors(form)

            data = form.cleaned_data
            data['bango'] = resp.bango
            view.client('UpdateRating', data)

        return Response(SellerProductBangoSerializer(product).data)
