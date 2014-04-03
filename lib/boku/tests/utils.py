import uuid
from django.core.urlresolvers import reverse

from lib.sellers.models import Seller
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
