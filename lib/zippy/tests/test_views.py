import json

from django.core.urlresolvers import reverse
from django.test import Client

from nose.tools import eq_, ok_
from test_utils import RequestFactory, TestCase

from ..views import ProxyView, NoReference


class FakeView(ProxyView):

    def get(self, request, *args, **kwargs):
        raise NoReference


class TestZippyView(TestCase):

    def test_no_reference(self):
        req = RequestFactory().get('/')
        eq_(FakeView().dispatch(req, reference_name='bob',
                                resource_name='sellers').status_code, 404)


class TestAPIView(TestCase):

    def test_no_reference(self):
        req = RequestFactory().get('/')
        with self.settings(ZIPPY_MOCK=False):
            eq_(ProxyView().dispatch(req, reference_name='bob',
                                     resource_name='sellers').status_code, 404)


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.seller_uuid = 'zippy-seller-uuid'
        self.product_uuid = 'zippy-product-uuid'

    def url_list(self, resource_name):
        return reverse('zippy.api_view', args=['reference', resource_name])

    def url_item(self, resource_name, pk):
        return reverse('zippy.api_view', args=['reference', resource_name, pk])

    def create_seller(self):
        seller = {
            'uuid': self.seller_uuid,
            'status': 'ACTIVE',
            'name': 'John',
            'email': 'jdoe@example.org',
        }
        self.client.post(self.url_list('sellers'), seller)
        seller.update({
            'resource_pk': '1',
            'resource_uri': '/sellers/1',
        })
        return seller

    def create_product(self, seller):
        product = {
            'seller_id': seller['resource_pk'],
            'external_id': self.product_uuid,
        }
        self.client.post(self.url_list('products'), product)
        product.update({
            'resource_pk': '1',
            'resource_uri': '/products/1',
        })
        return product

    def delete_seller(self):
        self.client.delete(self.url_item('sellers', self.seller_uuid))


class TestSellerViews(TestViews):

    def test_retrieve_sellers_empty(self):
        self.delete_seller()
        resp = self.client.get(self.url_list('sellers'))
        ok_(resp['Content-Type'].startswith('application/json'))
        eq_(json.loads(resp.content), [])

    def test_create_seller(self):
        seller = {
            'uuid': self.seller_uuid,
            'status': 'ACTIVE',
            'name': 'John',
            'email': 'jdoe@example.org',
        }
        resp = self.client.post(self.url_list('sellers'), seller)
        seller.update({
            'resource_pk': '1',
            'resource_uri': '/sellers/1',
        })
        eq_(json.loads(resp.content), seller)

    def test_retrieve_seller(self):
        seller = self.create_seller()
        resp = self.client.get(self.url_item('sellers', self.seller_uuid))
        eq_(json.loads(resp.content), seller)
        ok_(resp['Content-Type'].startswith('application/json'))

    def test_update_seller(self):
        seller = self.create_seller()
        new_name = 'Jack'
        resp = self.client.put(self.url_item('sellers', self.seller_uuid),
                               json.dumps({'name': new_name}),
                               content_type='application/json')
        seller.update({ 'name': new_name })
        eq_(json.loads(resp.content), seller)

    def test_delete_seller(self):
        self.create_seller()
        resp = self.client.delete(self.url_item('sellers', self.seller_uuid))
        eq_(resp.status_code, 200)


class TestProductViews(TestViews):

    def test_create_product(self):
        seller = self.create_seller()
        product = {
            'seller_id': seller['resource_pk'],
            'external_id': self.product_uuid,
        }
        resp = self.client.post(self.url_list('products'), product)
        product.update({
            'resource_pk': '1',
            'resource_uri': '/products/1',
        })
        eq_(json.loads(resp.content), product)


class TestTransactionViews(TestViews):

    def test_create_transaction(self):
        seller = self.create_seller()
        product = self.create_product(seller)
        transaction = {
            'product_id': product['resource_pk'],
            'region': '123',
            'carrier': 'USA_TMOBILE',
            'price': '0.99',
            'currency': 'EUR',
            'pay_method': 'OPERATOR'
        }
        resp = self.client.post(self.url_list('transactions'),
                                transaction)
        transaction.update({
            'resource_pk': '1',
            'resource_uri': '/transactions/1',
            'status': 'STARTED',
            'token': 'transaction-token',
        })
        eq_(json.loads(resp.content), transaction)

