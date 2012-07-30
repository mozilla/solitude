from lib.sellers.models import Seller, SellerBluevia, SellerPaypal


def make_seller_paypal(uuid):
    seller = Seller.objects.create(uuid=uuid)
    paypal = SellerPaypal.objects.create(seller=seller)
    return seller, paypal


def make_seller_bluevia(uuid):
    seller = Seller.objects.create(uuid=uuid)
    bluevia = SellerBluevia.objects.create(seller=seller,
                                           bluevia_id='something')
    return seller, bluevia
