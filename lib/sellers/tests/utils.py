from lib.sellers.models import Seller, SellerPaypal


def make_seller_paypal(uuid):
    seller = Seller.objects.create(uuid=uuid)
    paypal = SellerPaypal.objects.create(seller=seller)
    return seller, paypal
