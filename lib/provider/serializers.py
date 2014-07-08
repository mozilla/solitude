from django.core.urlresolvers import reverse

from rest_framework import serializers

from lib.sellers.models import (Seller, SellerReference,
                                SellerProduct, SellerProductReference)
from solitude.base import BaseSerializer, CompatRelatedField
from solitude.related_fields import PathRelatedField


class Remote(BaseSerializer):

    @property
    def remote_data(self):
        """Find out which data from the serializer is remote."""
        if not self.init_data:
            return
        return dict([k, v] for k, v in self.init_data.items()
                    if k in self.Meta.remote)

    def restore_object(self, attrs, instance=None):
        """Limit restoring an object to local values only."""
        new_attrs = dict([k, v] for k, v  in attrs.items()
                         if k not in self.Meta.remote)
        return (super(Remote, self)
                .restore_object(new_attrs, instance=instance))


class SellerReferenceSerializer(Remote, serializers.ModelSerializer):
    agreement = serializers.CharField(max_length=10)
    seller = CompatRelatedField(
        source='seller',
        tastypie={'resource_name': 'seller', 'api_name': 'generic'},
        view_name='api_dispatch_detail',
        queryset=Seller.objects.filter(),
    )
    uuid = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    status = serializers.ChoiceField(choices=(
        [s, s] for s in ['ACTIVE', 'INACTIVE', 'DISABLED']),
        required=True
    )

    class Meta:
        model = SellerReference
        fields = ('id', 'seller', 'resource_uri')
        remote = ['uuid', 'name', 'email', 'status', 'agreement']

    def get_resource_uri(self, obj):
        return reverse('provider.sellers',
                       kwargs={'id': obj.pk, 'reference_name': 'reference'})


class SellerProductReferenceSerializer(Remote, serializers.ModelSerializer):
    seller_product = CompatRelatedField(
        source='seller_product',
        tastypie={'resource_name': 'product', 'api_name': 'generic'},
        view_name='api_dispatch_detail',
        queryset=SellerProduct.objects.filter()
    )
    seller_reference = PathRelatedField(
        many=False,
        read_only=False,
        view_name='provider.sellers',
        lookup_field='id',
    )
    uuid = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)

    class Meta:
        model = SellerProductReference
        fields = ('id', 'seller_product', 'seller_reference', 'resource_uri')
        remote = ['uuid', 'external_id', 'name', 'seller_id']

    @property
    def remote_data(self):
        # Use the reference to the seller created in the reference
        # implementation.
        self.init_data['seller_id'] = self.object.seller_reference.reference_id
        # Use the external id from the seller_product.
        self.init_data['external_id'] = self.object.seller_product.external_id
        return super(SellerProductReferenceSerializer, self).remote_data

    def get_resource_uri(self, obj):
        return reverse('provider.products',
                       kwargs={'id': obj.pk, 'reference_name': 'reference'})


class TermsSerializer(Remote, serializers.ModelSerializer):
    agreement = serializers.CharField()
    text = serializers.CharField()

    class Meta:
        model = SellerReference
        fields = ['id', 'resource_uri']
        remote = ['text', 'agreement']

    @property
    def remote_data(self):
        return super(TermsSerializer, self).remote_data

    def get_resource_uri(self, obj):
        return reverse('provider.sellers',
            kwargs={'id': obj.pk, 'reference_name': 'reference'})

