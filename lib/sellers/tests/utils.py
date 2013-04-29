from lib.sellers.models import Seller, SellerPaypal, SellerProduct


def make_seller_paypal(uuid):
    seller = Seller.objects.create(uuid=uuid)
    product = SellerProduct.objects.create(seller=seller, external_id='xyz',
        public_id='some:id')
    paypal = SellerPaypal.objects.create(seller=seller)
    return seller, paypal, product
