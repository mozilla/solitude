import uuid

from django.core.urlresolvers import reverse

from lib.sellers.models import Seller, SellerProduct
from solitude.base import APITest


class SellerTest(APITest):

    def create_seller(self, **kwargs):
        defaults = {'uuid': 'seller:' + str(uuid.uuid4())}
        defaults.update(kwargs)
        return Seller.objects.create(**defaults)

    def get_seller_uri(self, seller):
        return reverse('generic:seller-detail', kwargs={'pk': seller.pk})

    def create_seller_product(self, seller=None, **kwargs):
        defaults = {
            'seller': seller or self.create_seller(),
            'public_id': 'public:' + str(uuid.uuid4()),
            'external_id': 'external:' + str(uuid.uuid4()),
        }
        defaults.update(kwargs)

        return SellerProduct.objects.create(**defaults)

    def get_seller_product_uri(self, seller_product):
        return seller_product.get_uri()
