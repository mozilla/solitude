from rest_framework import serializers

from lib.sellers.models import SellerBoku, SellerProductBoku
from solitude.related_fields import PathIdentityField, PathRelatedField


class SellerBokuSerializer(serializers.ModelSerializer):
    seller = PathRelatedField(view_name='generic:seller-detail')
    resource_uri = PathIdentityField(
        view_name='boku:sellerboku-detail'
    )

    class Meta:
        model = SellerBoku
        fields = ('id', 'seller', 'service_id', 'resource_uri')


class SellerProductBokuSerializer(serializers.ModelSerializer):
    seller_product = PathRelatedField(view_name='generic:sellerproduct-detail')
    seller_boku = PathRelatedField(
        many=False,
        read_only=False,
        view_name='boku:sellerboku-detail',
    )
    resource_uri = PathIdentityField(
        view_name='boku:sellerproductboku-detail'
    )

    class Meta:
        model = SellerProductBoku
        fields = ('id', 'seller_product', 'seller_boku', 'resource_uri')
