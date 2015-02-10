import uuid

from django import test
from django.core.urlresolvers import reverse

from lib.boku import constants
from lib.sellers.models import Seller, SellerBoku, SellerProduct
from lib.sellers.tests.utils import SellerTest
from lib.transactions.constants import PROVIDER_BOKU
from lib.transactions.models import Transaction


class SellerBokuTest(SellerTest):

    def setUp(self):
        super(SellerBokuTest, self).setUp()
        self.seller = self.create_seller()
        self.seller_uri = self.get_seller_uri(self.seller)

        self.example_service_id = '67890'
        self.seller_data = {
            'seller': self.seller_uri,
            'service_id': self.example_service_id,
        }

    def create_seller_boku(self, seller=None, **kwargs):
        defaults = {
            'seller': seller or self.create_seller(),
            'service_id': 'abc',
        }
        defaults.update(kwargs)

        return SellerBoku.objects.create(**defaults)

    def get_seller_boku_uri(self, seller_boku):
        return reverse(
            'boku:sellerboku-detail',
            args=(seller_boku.pk,)
        )


class SellerProductBokuTest(SellerBokuTest):

    def setUp(self):
        super(SellerProductBokuTest, self).setUp()
        self.seller_product = self.create_seller_product(seller=self.seller)
        self.seller_product_uri = self.get_seller_product_uri(
            self.seller_product)

        self.seller_boku = self.create_seller_boku(seller=self.seller)
        self.seller_boku_uri = self.get_seller_boku_uri(self.seller_boku)

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


class BokuTransactionTest(test.TestCase):

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
            'country': constants.COUNTRY_CHOICES[0][0],  # MX
            'transaction_uuid': self.transaction_uuid,
            'product_name': 'Django Pony',
            'price': '15.00',
            'currency': 'MXN',
            'seller_uuid': self.seller_uuid,
            'user_uuid': self.user_uuid,
        }


class BokuVerifyServiceTest(test.TestCase):

    def setUp(self):
        self.post_data = {'service_id': 'abc'}
