from django.db import models

from .constants import STATUS_CHOICES, STATUS_UNKNOWN
from lib.sellers.models import SellerProductBango
from solitude.base import Model


class Status(Model):
    status = models.IntegerField(choices=STATUS_CHOICES,
                                 default=STATUS_UNKNOWN)
    errors = models.TextField()
    seller_product_bango = models.ForeignKey(SellerProductBango,
                                             related_name='status')

    class Meta(Model.Meta):
        db_table = 'status_bango'
