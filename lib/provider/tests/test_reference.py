import json

from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.sellers.models import SellerReference
from lib.sellers.tests.utils import SellerTest


class TestSellerProductView(SellerTest):

    def setUp(self):
        self.seller = self.create_seller()
        self.product = self.create_seller_product(seller=self.seller)
        self.data = {
            'seller':
                self.get_detail_url('seller', self.seller, api_name='generic')
            }

    def test_ok(self):
        url = reverse('ref:sellerreference-list')
        response = self.client.post(url, data=self.data)
        eq_(response.status_code, 201, response.content)

        id = json.loads(response.content)['id']
        url = reverse('ref:sellerreference-detail', args=[id])
        response = self.client.get(url)
        eq_(response.status_code, 200, response.content)


class TestSellerProductReferenceView(SellerTest):

    def setUp(self):
        self.seller = self.create_seller()
        self.product = self.create_seller_product(seller=self.seller)
        self.ref = SellerReference.objects.create(seller=self.seller)
        self.data = {
            'seller_product':
                self.get_detail_url('product', self.product,
                                    api_name='generic'),
            'seller_reference':
                reverse('ref:sellerreference-detail', args=[self.ref.id])
            }

    def test_ok(self):
        url = reverse('ref:sellerproductreference-list')
        response = self.client.post(url, data=self.data)
        eq_(response.status_code, 201, response.content)

        id = json.loads(response.content)['id']
        url = reverse('ref:sellerproductreference-detail', args=[id])
        response = self.client.get(url)
        eq_(response.status_code, 200, response.content)
