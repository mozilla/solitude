from django.db import models

from aesfield.field import AESField

from solitude.base import Model
from .constants import EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE


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


class SellerProduct(Model):
    # An identifier for this product that corresponds to the
    # seller's catalog.
    external_id = models.CharField(max_length=255, db_index=True)
    seller = models.ForeignKey(Seller, related_name='product')
    # A generic secret field that can be used for this product, regardless
    # of backend.
    secret = AESField(blank=True, null=True,
                      aes_key='sellerproduct:secret')

    unique_error_message = lambda *args: EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE

    class Meta(Model.Meta):
        db_table = 'seller_product'
        unique_together = (('seller', 'external_id'),)


class SellerBango(Model):
    seller = models.OneToOneField(Seller, related_name='bango')
    package_id = models.IntegerField(unique=True)
    admin_person_id = models.IntegerField()
    support_person_id = models.IntegerField()
    finance_person_id = models.IntegerField()

    class Meta(Model.Meta):
        db_table = 'seller_bango'


class SellerProductBango(Model):
    seller_product = models.OneToOneField(SellerProduct,
                                          related_name='product')
    seller_bango = models.ForeignKey(SellerBango, related_name='bango')
    bango_id = models.CharField(max_length=50)

    class Meta(Model.Meta):
        db_table = 'seller_product_bango'
