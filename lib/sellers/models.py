from django.db import models

from aesfield.field import AESField


class Seller(models.Model):
    uuid = models.CharField(max_length=255, db_index=True, unique=True)

    class Meta:
        db_table = 'seller'


class SellerPaypal(models.Model):
    # TODO(andym): encrypt these based upon
    # https://bugzilla.mozilla.org/show_bug.cgi?id=763103
    paypal_id = AESField(max_length=255, blank=True, null=True,
                         aes_key='sellerpaypal:id')
    token = AESField(max_length=255, blank=True, null=True,
                     aes_key='sellerpaypal:token')
    secret = AESField(max_length=255, blank=True, null=True,
                      aes_key='sellerpaypal:secret')
    seller = models.OneToOneField(Seller, related_name='paypal')
    # TODO: currencies.

    class Meta:
        db_table = 'seller_paypal'

    @property
    def secret_exists(self):
        return bool(self.secret)

    @property
    def token_exists(self):
        return bool(self.token)
