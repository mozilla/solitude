from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.bango.serializers import SellerBangoSerializer
from lib.sellers.constants import EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE
from lib.sellers.models import Seller, SellerBango, SellerProduct
from solitude.base import BaseSerializer
from solitude.related_fields import PathRelatedField


class SellerSerializer(BaseSerializer):
    bango = PathRelatedField(
        view_name='bango:package-detail',
        read_only=True
    )

    class Meta:
        model = Seller

    def transform_bango(self, obj, value):
        # This makes me so sad that we did this. Please not again.
        # https://github.com/mozilla/solitude/issues/343
        try:
            seller_bango = SellerBango.objects.get(seller=obj)
            return SellerBangoSerializer(seller_bango).data
        except ObjectDoesNotExist:
            return {}

    def resource_uri(self, pk):
        return reverse('generic:seller-detail', kwargs={'pk': pk})


class SellerProductSerializer(BaseSerializer):
    seller_uuids = serializers.CharField(source='supported_providers',
                                         read_only=True)
    seller = PathRelatedField(
        view_name='generic:seller-detail',
        lookup_field='pk'
    )

    class Meta:
        model = SellerProduct
        # Note: fields are validated in this order, ensure that
        # external_id is after seller.
        fields = [
            'seller', 'access', 'resource_uri', 'resource_pk', 'secret',
            'seller_uuids', 'public_id', 'external_id',
        ]

    def validate_external_id(self, attrs, source):
        value = attrs.get(source)
        seller = attrs.get('seller')

        qs = SellerProduct.objects.filter(external_id=value)
        if seller:
            qs = qs.filter(seller=seller)

        if self.object:
            qs = qs.exclude(pk=self.object.pk)

        if qs.exists():
            raise serializers.ValidationError(
                EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE)

        return attrs

    def resource_uri(self, pk):
        return reverse('generic:sellerproduct-detail', kwargs={'pk': pk})
