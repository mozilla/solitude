from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.bango.models import Status
from lib.sellers.models import Seller, SellerBango, SellerProductBango
from lib.transactions.models import Transaction
from solitude.base import BaseSerializer
from solitude.related_fields import PathRelatedField

# Serializers are for serializing solitude data, basically models
# in all their different ways.
#
# If you'd like to validate Bango data, then please look at forms.py.


class PackageSerializer(serializers.Serializer):
    seller = PathRelatedField(
        view_name='generic:seller-detail', required=True,
        queryset=Seller.objects.filter())


class SellerBangoSerializer(BaseSerializer):

    class Meta:
        model = SellerBango

    def resource_uri(self, pk):
        return reverse('bango:package-detail', kwargs={'pk': pk})


class SellerProductBangoSerializer(BaseSerializer):
    seller_product = PathRelatedField(
        view_name='generic:sellerproduct-detail', required=False)

    seller_bango = PathRelatedField(
        view_name='bango:package-detail')

    bango_id = serializers.CharField(read_only=True)

    class Meta:
        model = SellerProductBango

    def resource_uri(self, pk):
        return reverse('bango:product-detail', kwargs={'pk': pk})


class SellerBangoOnly(serializers.Serializer):
    seller_bango = PathRelatedField(
        view_name='bango:package-detail', required=True,
        queryset=SellerBango.objects.filter())


class SellerProductBangoOnly(serializers.Serializer):
    seller_product_bango = PathRelatedField(
        view_name='bango:product-detail', required=True,
        queryset=SellerProductBango.objects.filter())


class RefundSerializer(BaseSerializer):
    status = serializers.CharField(source='_bango_refund_response_code',
                                   read_only=True)

    class Meta:
        model = Transaction
        fields = ['status', 'resource_uri', 'resource_pk', 'uuid']

    def resource_pk(self, obj):
        return obj.pk

    def uuid(self, obj):
        return obj.uuid

    def resource_uri(self, pk):
        return (reverse('bango:refund-list')
                + '?uuid={0}'.format(self.object.uuid))

    def transform_transaction(self, obj, value):
        return reverse('generic:transaction-detail',
                       kwargs={'pk': self.object.id})


class SBISerializer(serializers.Serializer):
    text = serializers.CharField()
    valid = serializers.DateTimeField()
    expires = serializers.DateTimeField()
    accepted = serializers.DateTimeField()


class StatusSerializer(BaseSerializer):
    seller_product_bango = PathRelatedField(
        view_name='bango:product-detail', required=True,
        queryset=SellerProductBango.objects.filter())
    status = PathRelatedField(
        view_name='bango:status-detail', read_only=True)

    class Meta:
        model = Status
        read_only_fields = ('errors', 'created', 'modified')

    def resource_uri(self, pk):
        return reverse('bango:status-detail', kwargs={'pk': pk})


class EasyObject(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
