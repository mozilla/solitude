from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.sellers.models import SellerBoku, SellerProductBoku
from ..serializers import SellerBokuSerializer, SellerProductBokuSerializer
from .utils import SellerBokuTest, SellerProductBokuTest


class SellerBokuSerializerTests(SellerBokuTest):

    def test_seller_required(self):
        del self.seller_data['seller']

        serializer = SellerBokuSerializer(data=self.seller_data)
        eq_(serializer.is_valid(), False)

    def test_service_id_required(self):
        del self.seller_data['service_id']

        serializer = SellerBokuSerializer(data=self.seller_data)
        eq_(serializer.is_valid(), False)

    def test_valid_data_creates_new_boku_seller(self):
        serializer = SellerBokuSerializer(data=self.seller_data)
        eq_(serializer.is_valid(), True)
        serializer.save()
        seller_boku = SellerBoku.objects.get(pk=serializer.object.pk)
        eq_(seller_boku.seller, self.seller)
        eq_(seller_boku.service_id, self.seller_data['service_id'])

    def test_serializer_outputs_correct_data(self):
        seller_boku = SellerBoku.objects.create(
            seller=self.seller,
            service_id='12345'
        )

        serializer = SellerBokuSerializer(seller_boku)
        eq_(serializer.data['id'], seller_boku.pk)
        eq_(serializer.data['seller'], self.seller_uri)
        eq_(serializer.data['service_id'], seller_boku.service_id)
        eq_(serializer.data['resource_uri'],
            reverse('boku:sellerboku-detail', kwargs={'pk': seller_boku.pk}))


class SellerProductBokuSerializerTests(SellerProductBokuTest):

    def test_seller_boku_required(self):
        del self.seller_product_boku_data['seller_boku']

        serializer = SellerProductBokuSerializer(
            data=self.seller_product_boku_data)
        eq_(serializer.is_valid(), False)

    def test_seller_product_required(self):
        del self.seller_product_boku_data['seller_product']

        serializer = SellerProductBokuSerializer(
            data=self.seller_product_boku_data)
        eq_(serializer.is_valid(), False)

    def test_valid_data_creates_new_seller_product_boku(self):
        serializer = SellerProductBokuSerializer(
            data=self.seller_product_boku_data)
        eq_(serializer.is_valid(), True)
        serializer.save()
        seller_product_boku = SellerProductBoku.objects.get(
            pk=serializer.object.pk)
        eq_(seller_product_boku.seller_product, self.seller_product)
        eq_(seller_product_boku.seller_boku, self.seller_boku)

    def test_serializer_outputs_correct_data(self):
        seller_product_boku = SellerProductBoku.objects.create(
            seller_product=self.seller_product,
            seller_boku=self.seller_boku,
        )

        serializer = SellerProductBokuSerializer(seller_product_boku)
        eq_(serializer.data['id'], seller_product_boku.pk)
        eq_(serializer.data['seller_product'], self.seller_product_uri)
        eq_(serializer.data['seller_boku'], self.seller_boku_uri)
        eq_(serializer.data['resource_uri'],
            reverse('boku:sellerproductboku-detail',
                    kwargs={'pk': seller_product_boku.pk}))
