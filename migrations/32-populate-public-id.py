import uuid

from django.db.utils import DatabaseError

from lib.sellers.models import SellerProduct


def run():
    try:
        for seller in SellerProduct.objects.all():
            seller.public_id = str(uuid.uuid4())
            seller.save()
    except DatabaseError, exc:
        if "Unknown column 'seller_product.access'" in str(exc):
            # We don't need to worry about this migration then.
            return
        raise
