from rest_framework import serializers

from lib.sellers.models import (Seller, SellerReference,
                                SellerProduct, SellerProductReference)
from solitude.base import CompatRelatedField
from solitude.related_fields import PathRelatedField, PathIdentityField


class SellerReferenceSerializer(serializers.ModelSerializer):
    seller = CompatRelatedField(
        source='seller',
        tastypie={'resource_name': 'seller','api_name': 'generic'},
        view_name='api_dispatch_detail',
        queryset=Seller.objects.filter()
    )
    resource_uri = PathIdentityField(
        view_name='ref:sellerreference-detail'
    )

    class Meta:
        model = SellerReference
        fields = ('id', 'seller', 'resource_uri')


class SellerProductReferenceSerializer(serializers.ModelSerializer):
    seller_product = CompatRelatedField(
        source='seller_product',
        tastypie={'resource_name': 'product', 'api_name': 'generic'},
        view_name='api_dispatch_detail',
        queryset=SellerProduct.objects.filter()
    )
    seller_reference = PathRelatedField(
        many=False,
        read_only=False,
        view_name='ref:sellerreference-detail',
    )
    resource_uri = PathIdentityField(
        view_name='ref:sellerproductreference-detail'
    )

    class Meta:
        model = SellerProductReference
        fields = ('id', 'seller_product', 'seller_reference', 'resource_uri')
