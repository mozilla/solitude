from django.core.urlresolvers import reverse

from rest_framework.response import Response

from lib.bango.resources.cached import BangoResource
from lib.bango.forms import (CreateBangoNumberForm, MakePremiumForm,
                             UpdateRatingForm)
from lib.sellers.models import SellerBango, SellerProduct, SellerProductBango

from solitude.base import BaseAPIView, BaseSerializer, CompatRelatedField


class SellerProductBangoSerializer(BaseSerializer):
    # So that seller_product and seller_bango resolve to the correct
    # tastypie instances.
    seller_product = CompatRelatedField(
        source='seller_product',
        tastypie={'resource_name': 'product', 'api_name': 'generic'},
        view_name='api_dispatch_detail',
        queryset=SellerProduct.objects.filter())
    seller_bango = CompatRelatedField(
        source='seller_bango',
        tastypie={'resource_name': 'product', 'api_name': 'bango'},
        view_name='api_dispatch_detail',
        queryset=SellerBango.objects.filter())

    class Meta:
        model = SellerProductBango

    def resource_uri(self, pk):
        # So that resource_uri knows to resolve to itself.
        return reverse('api_dispatch_detail', kwargs={
            'api_name': 'bango', 'resource_name': 'product', 'pk': pk})


class ProductView(BaseAPIView, BangoResource):
    """
    Override creating a product.
    """

    def post(self, request, *args, **kwargs):
        form = CreateBangoNumberForm(request.DATA)
        if not form.is_valid():
            return self.form_errors(form)

        # Create the product.
        resp = self.client('CreatePackage', form.bango_data)
        product = SellerProductBango.objects.create(
            seller_bango=form.cleaned_data['seller_bango'],
            seller_product=form.cleaned_data['seller_product'],
            bango_id=resp.bango,
        )

        # Make it premium.
        data = request.DATA.copy()
        data['seller_product_bango'] = reverse('api_dispatch_detail',
                kwargs={'resource_name': 'product',
                        'api_name': 'generic',
                        'pk': product.pk})
        data['price'] = '0.99'
        data['currencyIso'] = 'USD'

        form = MakePremiumForm(data)
        if not form.is_valid():
            return self.form_errors(form)

        self.client('MakePremiumPerAccess', form.bango_data)

        for rating, scheme in (['UNIVERSAL', 'GLOBAL'],
                               ['GENERAL', 'USA']):
            # Make it global and US rating.
            data.update({'rating': rating, 'ratingScheme': scheme})
            form = UpdateRatingForm(data)
            if not form.is_valid():
                return self.form_errors(form)

            self.client('UpdateRating', form.bango_data)

        return Response(SellerProductBangoSerializer(product).data)
