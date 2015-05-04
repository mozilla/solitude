from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_

from slumber.exceptions import HttpServerError
from lib.sellers.models import SellerProductReference, SellerReference
from lib.sellers.tests.utils import SellerTest

REF_ID = 'some:ref:id'


class TestSellerProductView(SellerTest):

    def setUp(self):
        self.seller = self.create_seller()
        self.data = {
            'seller': self.seller.get_uri(),
            'uuid': 'some:uid',
            'name': 'bob',
            'email': 'f@b.c',
            'status': 'ACTIVE'
        }
        self.url = reverse('reference:sellers-list')

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

        url = reverse('reference:sellers-detail', kwargs={'pk': ref.pk})
        response = self.client.get(url)
        eq_(response.status_code, 200, response.content)


class TestSellerProductReferenceView(SellerTest):

    def setUp(self):
        self.seller = self.create_seller()
        self.product = self.create_seller_product(seller=self.seller)
        self.ref = SellerReference.objects.create(seller=self.seller,
                                                  reference_id='ref:id')
        self.data = {
            'seller_product': self.product.get_uri(),
            'seller_reference':
                reverse('reference:sellers-detail', args=[self.ref.id]),
            'name': 'bob',
            'uuid': 'some:uuid'
        }
        self.url = reverse('reference:products-list')

        p = patch('lib.provider.client.APIMockObject.post')
        self.provider_post = p.start()
        self.addCleanup(p.stop)

        p = patch('lib.provider.client.APIMockObject.get_data')
        self.provider_get = p.start()
        self.addCleanup(p.stop)

    def create_provider_product(self, **kw):
        props = dict(seller_product=self.product,
                     seller_reference=self.ref,
                     reference_id=REF_ID)
        props.update(kw)
        return SellerProductReference.objects.create(**props)

    def test_post(self):
        self.provider_post.return_value = {'uuid': 'some:uid'}
        response = self.client.post(self.url, data=self.data)
        eq_(response.status_code, 201, response.content)

    def test_post_external_id(self):
        self.provider_post.return_value = {'uuid': 'some:uid'}
        self.client.post(self.url, data=self.data)
        self.provider_post.assert_called_with({
            'seller_id': 'ref:id',
            'external_id': self.product.external_id,
            'uuid': 'some:uuid',
            'name': 'bob'
        })

    def test_get(self):
        ref = self.create_provider_product()
        self.provider_get.return_value = {REF_ID: {'f': 'b'}}

        url = reverse('reference:products-detail', args=[ref.id])
        response = self.client.get(url)
        eq_(response.status_code, 200, response.content)

    def test_filter_sellers_by_uuid(self):
        self.create_provider_product()

        url = reverse('reference:sellers-list')
        response = self.client.get(url, {'seller__uuid': self.seller.uuid})

        eq_(response.status_code, 200, response.content)
        eq_(response.data['objects'][0]['id'], self.ref.pk)
        eq_(response.data['meta']['total_count'], 1)

    def test_filter_by_ext_id(self):
        self.create_provider_product()
        decoy_sel = self.create_seller()
        ext_id = 'my-fancy-ext-id'
        decoy_prod = self.create_seller_product(seller=decoy_sel,
                                                external_id=ext_id)
        decoy = self.create_provider_product(seller_product=decoy_prod)

        url = reverse('reference:products-list')
        response = self.client.get(url, {
            'seller_product__seller': decoy_sel.pk,
            'seller_product__external_id': ext_id})

        eq_(response.status_code, 200, response.content)
        eq_(response.data['objects'][0]['id'], decoy.pk)
        eq_(response.data['meta']['total_count'], 1)


class TestTermsView(SellerTest):

    def setUp(self):
        self.seller = self.create_seller()
        self.ref = SellerReference.objects.create(seller=self.seller,
                                                  reference_id=REF_ID)
        self.url = reverse('reference:terms-detail',
                           kwargs={'pk': self.ref.pk})

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
