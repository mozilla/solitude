import json
import urllib
import uuid

from django.core.urlresolvers import reverse

import mock
from nose.tools import eq_, ok_

from lib.boku.tests.utils import (BokuTransactionTest, BokuVerifyServiceTest,
                                  SellerBokuTest, SellerProductBokuTest)
from lib.sellers.models import (Seller, SellerBoku,
                                SellerProduct, SellerProductBoku)


class TestSellerBokuViews(SellerBokuTest):

    def test_list_view_lists_all_sellers(self):
        for i in range(3):
            seller = Seller.objects.create(uuid=str(uuid.uuid4()))
            SellerBoku.objects.create(
                seller=seller,
                service_id=self.example_service_id,
            )

        response = self.client.get(reverse('boku:sellerboku-list'))
        eq_(response.status_code, 200, response.content)
        sellers_data = json.loads(response.content)
        eq_(len(sellers_data['objects']), 3)

    def test_create_view_creates_seller_boku(self):
        response = self.client.post(
            reverse('boku:sellerboku-list'), data=self.seller_data
        )
        eq_(response.status_code, 201, response.content)
        seller_boku_data = json.loads(response.content)

        seller_boku = SellerBoku.objects.get(pk=seller_boku_data['id'])
        eq_(seller_boku.seller, self.seller)
        eq_(seller_boku.service_id, self.seller_data['service_id'])

    def test_detail_view_returns_seller_boku(self):
        seller_boku = SellerBoku.objects.create(
            seller=self.seller,
            service_id=self.example_service_id,
        )
        response = self.client.get(
            reverse('boku:sellerboku-detail', kwargs={'pk': seller_boku.pk}),
        )
        eq_(response.status_code, 200, response.content)

        seller_boku_data = json.loads(response.content)
        eq_(seller_boku_data['id'], seller_boku.pk)
        eq_(seller_boku_data['seller'], self.seller_uri)
        eq_(seller_boku_data['service_id'], seller_boku.service_id)
        eq_(
            seller_boku_data['resource_uri'],
            reverse(
                'boku:sellerboku-detail',
                kwargs={'pk': seller_boku.pk},
            )
        )

    def test_update_view_modifies_existing_seller_boku(self):
        new_service_id = '54321'
        seller_boku = SellerBoku.objects.create(
            seller=self.seller,
            service_id=self.example_service_id,
        )
        response = self.client.patch(
            reverse('boku:sellerboku-detail', kwargs={'pk': seller_boku.pk}),
            data={'service_id': new_service_id},
        )
        eq_(response.status_code, 200, response.content)

        seller_boku = SellerBoku.objects.get(pk=seller_boku.pk)
        eq_(seller_boku.service_id, new_service_id)

    def test_delete_not_allowed(self):
        seller_boku = SellerBoku.objects.create(
            seller=self.seller,
            service_id=self.example_service_id,
        )
        response = self.client.delete(
            reverse('boku:sellerboku-detail', kwargs={'pk': seller_boku.pk})
        )
        eq_(response.status_code, 403, response.content)


class TestSellerProductBokuViews(SellerProductBokuTest):

    def create_seller_product_boku(self):
        seller = Seller.objects.create(uuid=str(uuid.uuid4()))
        seller_boku = SellerBoku.objects.create(seller=seller)
        seller_product = SellerProduct.objects.create(
            seller=seller,
            public_id=str(uuid.uuid4()),
            external_id=str(uuid.uuid4()),
        )
        return SellerProductBoku.objects.create(
            seller_boku=seller_boku,
            seller_product=seller_product,
        )

    def test_list_view_lists_all_seller_products(self):
        for i in range(3):
            self.create_seller_product_boku()

        response = self.client.get(reverse('boku:sellerproductboku-list'))
        eq_(response.status_code, 200, response.content)
        sellers_data = json.loads(response.content)
        eq_(len(sellers_data['objects']), 3)

    def test_list_view_allows_filtering_on_generic_product(self):
        seller_product_boku = self.create_seller_product_boku()
        for i in range(2):
            self.create_seller_product_boku()

        list_all_url = reverse('boku:sellerproductboku-list')
        list_filter_url = '{path}?{query}'.format(
            path=list_all_url,
            query=urllib.urlencode({
                'seller_product': seller_product_boku.seller_product.pk,
            })
        )

        response = self.client.get(list_all_url)
        eq_(response.status_code, 200, response.content)
        sellers_data = json.loads(response.content)
        eq_(
            sorted([seller['id'] for seller in sellers_data['objects']]),
            sorted([seller.id for seller in SellerProductBoku.objects.all()]),
        )

        response = self.client.get(list_filter_url)
        eq_(response.status_code, 200, response.content)
        sellers_data = json.loads(response.content)
        eq_(
            [seller['id'] for seller in sellers_data['objects']],
            [seller_product_boku.id]
        )

    def test_create_view_creates_seller_product_boku(self):
        response = self.client.post(
            reverse('boku:sellerproductboku-list'),
            data=self.seller_product_boku_data
        )

        eq_(response.status_code, 201, response.content)
        seller_product_boku_data = json.loads(response.content)

        seller_product_boku = SellerProductBoku.objects.get(
            pk=seller_product_boku_data['id'])
        eq_(seller_product_boku.seller_boku, self.seller_boku)
        eq_(seller_product_boku.seller_product, self.seller_product)

    def test_create_multiple_seller_product_boku_for_same_seller_product(self):
        list_url = reverse('boku:sellerproductboku-list')

        product1 = self.create_seller_product()
        product1_uri = self.get_seller_product_uri(product1)

        product2 = self.create_seller_product()
        product2_uri = self.get_seller_product_uri(product2)

        post_data1 = {
            'seller_product': product1_uri,
            'seller_boku': self.seller_boku_uri,
        }

        response = self.client.post(list_url, data=post_data1)
        eq_(response.status_code, 201, response.content)
        ok_(SellerProductBoku.objects.filter(
            seller_product=product1,
            seller_boku=self.seller_boku).exists())

        post_data2 = {
            'seller_product': product2_uri,
            'seller_boku': self.seller_boku_uri,
        }

        response = self.client.post(list_url, data=post_data2)
        eq_(response.status_code, 201, response.content)
        ok_(SellerProductBoku.objects.filter(
            seller_product=product2,
            seller_boku=self.seller_boku).exists())

    def test_detail_view_returns_seller_product_boku(self):
        seller_product_boku = SellerProductBoku.objects.create(
            seller_boku=self.seller_boku,
            seller_product=self.seller_product,
        )
        seller_product_boku_uri = reverse(
            'boku:sellerproductboku-detail',
            kwargs={'pk': seller_product_boku.pk},
        )
        response = self.client.get(seller_product_boku_uri)
        eq_(response.status_code, 200, response.content)

        seller_product_boku_data = json.loads(response.content)
        eq_(seller_product_boku_data['id'], seller_product_boku.pk)
        eq_(seller_product_boku_data['seller_boku'], self.seller_boku_uri)
        eq_(seller_product_boku_data['seller_product'],
            self.seller_product_uri)
        eq_(seller_product_boku_data['resource_uri'], seller_product_boku_uri)

    def test_update_view_modifies_existing_seller_product_boku(self):
        new_seller_product = SellerProduct.objects.create(
            seller=self.seller,
            public_id=str(uuid.uuid4()),
            external_id=str(uuid.uuid4()),
        )
        new_seller_product_uri = new_seller_product.get_uri()

        seller_product_boku = SellerProductBoku.objects.create(
            seller_boku=self.seller_boku,
            seller_product=self.seller_product,
        )
        response = self.client.patch(
            reverse('boku:sellerproductboku-detail',
                    kwargs={'pk': seller_product_boku.pk}),
            data={'seller_product': new_seller_product_uri},
        )
        eq_(response.status_code, 200, response.content)

        seller_product_boku = SellerProductBoku.objects.get(
            pk=seller_product_boku.pk)
        eq_(seller_product_boku.seller_product, new_seller_product)

    def test_delete_removes_seller_product_boku(self):
        seller_product_boku = SellerProductBoku.objects.create(
            seller_boku=self.seller_boku,
            seller_product=self.seller_product,
        )
        response = self.client.delete(
            reverse('boku:sellerproductboku-detail',
                    kwargs={'pk': seller_product_boku.pk})
        )
        eq_(response.status_code, 204, response.content)
        ok_(not SellerProductBoku.objects
                                 .filter(pk=seller_product_boku.pk)
                                 .exists())


class TestBokuTransactionView(BokuTransactionTest):

    def setUp(self):
        super(TestBokuTransactionView, self).setUp()
        self.url = reverse('boku:start_transaction')

    def test_valid_data_starts_transaction(self):
        response = self.client.post(self.url, data=self.post_data)
        eq_(response.status_code, 200, response.content)

        transaction_data = json.loads(response.content)
        ok_('transaction_id' in transaction_data)

    def test_invalid_data_returns_form_errors(self):
        self.post_data['callback_url'] = 'foo'
        response = self.client.post(self.url, data=self.post_data)
        eq_(response.status_code, 400, response.content)

        transaction_data = json.loads(response.content)
        eq_(transaction_data['callback_url'], ['Enter a valid URL.'])


class TestBokuVerifyServiceView(BokuVerifyServiceTest):

    def setUp(self):
        super(TestBokuVerifyServiceView, self).setUp()
        self.url = reverse('boku:verify_service')

    def test_valid_service_id_returns_204(self):
        response = self.client.post(self.url, data=self.post_data)
        eq_(response.status_code, 204, response.content)

    def test_invalid_service_id_returns_400(self):
        with mock.patch(
            'lib.boku.client.mocks',
            {'service-prices': (500, '')}
        ):
            response = self.client.post(self.url, data=self.post_data)
            eq_(response.status_code, 400, response.content)
