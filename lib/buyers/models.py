from django.db import models

from aesfield.field import AESField

from solitude.base import Model
from .field import HashField


class Buyer(Model):
    uuid = models.CharField(max_length=255, db_index=True, unique=True)
    pin = HashField(blank=True, null=True)
    pin_confirmed = models.BooleanField(default=False)

    class Meta(Model.Meta):
        db_table = 'buyer'


class BuyerPaypal(Model):
    key = AESField(blank=True, null=True, aes_key='buyerpaypal:key')
    expiry = models.DateField(blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    buyer = models.OneToOneField(Buyer, related_name='paypal')

    class Meta(Model.Meta):
        db_table = 'buyer_paypal'

    @property
    def key_exists(self):
        return bool(self.key)

    @key_exists.setter
    def key_exists(self, value):
        # This is bit warped. But we need to be able to remove the key
        # from the buyer. But we should never be setting this value. But we do
        # need to remove it. So if you pass an empty string, we ignore it.
        # Otherwise we leave it alone.
        self.key = None if not value else self.key
