from rest_framework import serializers

from solitude.base import CompatRelatedField
from lib.sellers.models import (Seller, SellerBoku,
                                SellerProduct, SellerProductBoku)


class SellerBokuSerializer(serializers.ModelSerializer):
    seller = CompatRelatedField(
        source='seller',
        tastypie={
            'resource_name': 'seller',
            'api_name': 'generic'
        },
        view_name='api_dispatch_detail',
        queryset=Seller.objects.filter()
    )
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='boku:sellerboku-detail'
    )

    class Meta:
        model = SellerBoku
        fields = ('id', 'seller', 'service_id', 'resource_uri')


class SellerProductBokuSerializer(serializers.ModelSerializer):
    seller_product = CompatRelatedField(
        source='seller_product',
        tastypie={
            'resource_name': 'product',
            'api_name': 'generic'
        },
        view_name='api_dispatch_detail',
        queryset=SellerProduct.objects.filter()
    )
    seller_boku = serializers.HyperlinkedRelatedField(
        many=False,
        read_only=False,
        view_name='boku:sellerboku-detail',
    )
    resource_uri = serializers.HyperlinkedIdentityField(
        view_name='boku:sellerproductboku-detail'
    )

    class Meta:
        model = SellerProductBoku
        fields = ('id', 'seller_product', 'seller_boku', 'resource_uri')
