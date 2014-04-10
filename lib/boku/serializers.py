from rest_framework import serializers

from solitude.base import CompatRelatedField
from lib.sellers.models import Seller, SellerBoku


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
        fields = ('id', 'seller', 'merchant_id', 'service_id', 'resource_uri')
