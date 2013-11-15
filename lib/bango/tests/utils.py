import collections

from lib.sellers.models import (Seller, SellerBango, SellerProduct,
                                SellerProductBango)

Sellers = collections.namedtuple('Seller', 'seller bango product')
SellerProducts = collections.namedtuple('SellerProduct',
                                        'product_bango seller bango product ')


def make_no_product(uuid='sample:uuid', bangoid='sample:bangoid'):
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
    return Sellers(seller, bango, product)


def make_sellers(uuid='sample:uuid', bangoid='sample:bangoid'):
    no = make_no_product(uuid=uuid, bangoid=bangoid)
    product_bango = SellerProductBango.objects.create(
        seller_product=no.product,
        seller_bango=no.bango,
        bango_id=bangoid,
    )
    return SellerProducts(product_bango, *no)
