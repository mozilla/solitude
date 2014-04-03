from django.db import models

from aesfield.field import AESField

from solitude.base import Model
from .constants import (ACCESS_CHOICES, ACCESS_PURCHASE,
                        EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE)


class Seller(Model):
    uuid = models.CharField(max_length=255, db_index=True, unique=True)
    active = models.BooleanField(default=True, db_index=True)

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
    """
    The key to a seller's generic product.
    """
    # An identifier for this product that corresponds to the
    # seller's catalog.
    external_id = models.CharField(max_length=255, db_index=True)
    # An publily visible id used in in-app payments so that we
    # can identify the seller. This will be the iss field in JWT.
    public_id = models.CharField(max_length=255, db_index=True, unique=True)
    seller = models.ForeignKey(Seller, related_name='product')
    # A generic secret field that can be used for this product, regardless
    # of backend.
    secret = AESField(blank=True, null=True,
                      aes_key='sellerproduct:secret')
    # The type of access this product key has.
    access = models.PositiveIntegerField(choices=ACCESS_CHOICES,
                                         default=ACCESS_PURCHASE)

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
    # There are a few fields around SBI, but all we really care about
    # is when it expires. We'll store this so we can quickly find out
    # all the people it is about to expire for.
    sbi_expires = models.DateTimeField(blank=True, null=True)

    class Meta(Model.Meta):
        db_table = 'seller_bango'


class SellerProductBango(Model):
    seller_product = models.OneToOneField(SellerProduct,
                                          related_name='product')
    seller_bango = models.ForeignKey(SellerBango, related_name='bango')
    bango_id = models.CharField(max_length=50)

    class Meta(Model.Meta):
        db_table = 'seller_product_bango'


class SellerBoku(Model):
    seller = models.OneToOneField(Seller, related_name='boku')
    merchant_id = models.CharField(max_length=255, blank=False, null=False)
    service_id = models.CharField(max_length=255, blank=False, null=False)

    class Meta(Model.Meta):
        db_table = 'seller_boku'
