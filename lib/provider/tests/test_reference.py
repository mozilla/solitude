from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_

from curling.lib import HttpServerError
from lib.sellers.models import SellerProductReference, SellerReference
from lib.sellers.tests.utils import SellerTest

REF_ID = 'some:ref:id'


class TestSellerProductView(SellerTest):

    def setUp(self):
        self.seller = self.create_seller()
        self.data = {
            'seller':
                self.get_detail_url('seller', self.seller, api_name='generic'),
            'uuid': 'some:uid',
            'name': 'bob',
            'email': 'f@b.c',
            'status': 'ACTIVE'
        }
        self.url = reverse('provider.sellers')

    def test_post(self):
        response = self.client.post(self.url, data=self.data)
        eq_(response.status_code, 201, response.content)

    @patch('lib.provider.client.APIMockObject.post')
    def test_not_valid(self, post):
        post.side_effect = HttpServerError
        with self.assertRaises(HttpServerError):
            self.client.post(self.url, data=self.data)

    @patch('lib.provider.client.APIMockObject.get_data')
    def test_get(self, get_data):
        ref = SellerReference.objects.create(seller=self.seller,
                                             reference_id=REF_ID)
        get_data.return_value = {REF_ID: {'f': 'b'}}

        url = reverse('provider.sellers', kwargs={'id': ref.pk})
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
                reverse('provider.sellers', args=[self.ref.id]),
            'name': 'bob',
            'uuid': 'some:uuid'
        }
        self.url = reverse('provider.products')

    def test_post(self):
        response = self.client.post(self.url, data=self.data)
        eq_(response.status_code, 201, response.content)

    @patch('lib.provider.client.APIMockObject.post')
    def test_post_external_id(self, post):
        post.return_value = {'uuid': 'some:uid'}
        self.client.post(self.url, data=self.data)
        post.assert_called_with({
            'seller_id': self.seller.uuid,
            'external_id': self.product.external_id,
            'uuid': 'some:uuid',
            'name': 'bob'
        })

    @patch('lib.provider.client.APIMockObject.get_data')
    def test_get(self, get_data):
        ref = SellerProductReference.objects.create(
            seller_product=self.product,
            seller_reference=self.ref,
            reference_id=REF_ID)
        get_data.return_value = {REF_ID: {'f': 'b'}}

        url = reverse('provider.products', args=[ref.id])
        response = self.client.get(url)
        eq_(response.status_code, 200, response.content)


class TestTermsView(SellerTest):

    def setUp(self):
        self.seller = self.create_seller()
        self.ref = SellerReference.objects.create(seller=self.seller,
                                                  reference_id=REF_ID)
        self.url = reverse('provider.terms', kwargs={'id': self.ref.pk})

    @patch('lib.provider.client.APIMockObject.get_data')
    def test_get(self, get_data):
        get_data.return_value = {REF_ID: {'agreement': '', 'detail': 'Terms'}}
        response = self.client.get(self.url)
        eq_(response.status_code, 200, response.content)

    @patch('lib.provider.client.APIMockObject.get_data')
    def test_put(self, get_data):
        get_data.return_value = {REF_ID: {'agreement': '', 'detail': 'Terms'}}
        response = self.client.put(self.url, data={'agreement': '2014-01-01'})
        eq_(response.status_code, 200, response.content)
