import uuid

from django.core.urlresolvers import reverse

import test_utils

from lib.boku import constants
from lib.sellers.models import Seller, SellerBoku, SellerProduct
from lib.transactions.constants import PROVIDER_BOKU
from lib.transactions.models import Transaction
from solitude.base import APITest


class SellerBokuTest(APITest):

    def setUp(self):
        super(SellerBokuTest, self).setUp()
        self.seller = Seller.objects.create(uuid=str(uuid.uuid4()))
        self.seller_uri = reverse(
            'api_dispatch_detail',
            kwargs={
                'api_name': 'generic',
                'resource_name': 'seller',
                'pk': self.seller.pk,
            }
        )
        self.example_service_id = '67890'
        self.seller_data = {
            'seller': self.seller_uri,
            'service_id': self.example_service_id,
        }


class SellerProductBokuTest(SellerBokuTest):

    def setUp(self):
        super(SellerProductBokuTest, self).setUp()
        self.seller_product = SellerProduct.objects.create(
            seller=self.seller,
            public_id=str(uuid.uuid4()),
            external_id=str(uuid.uuid4()),
        )
        self.seller_boku = SellerBoku.objects.create(
            seller=self.seller,
            service_id='abc',
        )

        self.seller_product_uri = reverse(
            'api_dispatch_detail',
            kwargs={
                'api_name': 'generic',
                'resource_name': 'product',
                'pk': self.seller_product.pk,
            }
        )
        self.seller_boku_uri = reverse(
            'boku:sellerboku-detail',
            args=(self.seller_boku.pk,)
        )

        self.seller_product_boku_data = {
            'seller_product': self.seller_product_uri,
            'seller_boku': self.seller_boku_uri,
        }


class EventTest(SellerBokuTest):

    def setUp(self):
        super(EventTest, self).setUp()
        self.product = SellerProduct.objects.create(seller=self.seller,
                                                    external_id='xyz')
        self.trans = Transaction.objects.create(uuid='some:uuid',
                                                provider=PROVIDER_BOKU,
                                                seller_product=self.product)

    def add_seller_boku(self):
        self.seller_boku = SellerBoku.objects.create(seller=self.seller,
                                                     service_id='456')

    def sample(self):
        return {
            'action': 'billingresult',
            'amount': '100',
            'currency': 'MXN',
            'param': 'some:uuid',
            'sig': 'some:sig',
            'trx-id': 'some:trxid'
        }


class BokuTransactionTest(test_utils.TestCase):

    def setUp(self):
        self.transaction_uuid = str(uuid.uuid4())
        self.seller_uuid = str(uuid.uuid4())
        self.user_uuid = str(uuid.uuid4())

        self.seller = Seller.objects.create(uuid=self.seller_uuid)
        self.seller_boku = SellerBoku.objects.create(
            seller=self.seller,
            service_id='service_id'
        )

        self.post_data = {
            'callback_url': 'http://testing.com/pay/notification',
            'forward_url': 'http://testing.com/pay/success',
            'country': constants.COUNTRY_CHOICES[0][0],
            'transaction_uuid': self.transaction_uuid,
            'price': '15.00',
            'seller_uuid': self.seller_uuid,
            'user_uuid': self.user_uuid,
        }


class BokuVerifyServiceTest(test_utils.TestCase):

    def setUp(self):
        self.post_data = {'service_id': 'abc'}
