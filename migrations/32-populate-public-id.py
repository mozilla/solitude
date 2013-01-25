import uuid

from lib.sellers.models import SellerProduct


def run():
    for seller in SellerProduct.objects.all():
        seller.public_id = str(uuid.uuid4())
        seller.save()
