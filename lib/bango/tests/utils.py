import collections

from lib.sellers.models import (Seller, SellerBango, SellerProduct,
                                SellerProductBango)


def make_sellers(uuid='sample:uuid', bangoid='sample:bangoid'):
    seller = Seller.objects.create(uuid=uuid)
    bango = SellerBango.objects.create(
        seller=seller,
        package_id=1,
        admin_person_id=3,
        support_person_id=3,
        finance_person_id=4,
    )
    product = SellerProduct.objects.create(
        seller=seller,
        external_id='xyz',
    )
    product_bango = SellerProductBango.objects.create(
        seller_product=product,
        seller_bango=bango,
        bango_id=bangoid,
    )
    Sellers = collections.namedtuple('Sellers',
                                     'seller bango product product_bango')
    return Sellers(seller, bango, product, product_bango)
