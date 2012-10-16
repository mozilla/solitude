from django.db import models

from aesfield.field import AESField

from solitude.base import Model


class Seller(Model):
    uuid = models.CharField(max_length=255, db_index=True, unique=True)

    class Meta(Model.Meta):
        db_table = 'seller'


class SellerPaypal(Model):
    paypal_id = AESField(blank=True, null=True, aes_key='sellerpaypal:id')
    token = AESField(blank=True, null=True, aes_key='sellerpaypal:token')
    secret = AESField(blank=True, null=True, aes_key='sellerpaypal:secret')
    seller = models.OneToOneField(Seller, related_name='paypal')
    # TODO: currencies.

    # Sellers personal contact information.
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    business_name = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=64, blank=True)
    address_one = models.CharField(max_length=255, blank=True)
    address_two = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=128, blank=True)
    city = models.CharField(max_length=128, blank=True)
    state = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=32, blank=True)

    class Meta(Model.Meta):
        db_table = 'seller_paypal'

    @property
    def secret_exists(self):
        return bool(self.secret)

    @property
    def token_exists(self):
        return bool(self.token)


class SellerBluevia(Model):
    bluevia_id = AESField(blank=True, null=True, aes_key='sellerbluevia:id')
    seller = models.OneToOneField(Seller, related_name='bluevia')

    class Meta(Model.Meta):
        db_table = 'seller_bluevia'


class SellerProduct(Model):
    seller = models.ForeignKey(Seller, related_name='product')
    bango_secret = AESField(blank=True, null=True,
                            aes_key='sellerproduct:bangosecret')

    class Meta(Model.Meta):
        db_table = 'seller_product'
