import uuid

from django.core.urlresolvers import reverse

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
        self.example_merchant_id = '12345'
        self.example_service_id = '67890'
        self.seller_data = {
            'seller': self.seller_uri,
            'merchant_id': self.example_merchant_id,
            'service_id': self.example_service_id,
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
                                                     merchant_id='123',
                                                     service_id='456')

    def sample(self):
        return {
            'action': 'billingresult',
            'amount': '1.00',
            'currency': 'MXN',
            'param': 'some:uuid',
            'sig': 'some:sig',
            'trx-id': 'some:trxid'
        }
