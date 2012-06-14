from django.db import models


class Seller(models.Model):
    uuid = models.CharField(max_length=255, db_index=True, unique=True)

    class Meta:
        db_table = 'seller'


class SellerPaypal(models.Model):
    # TODO(andym): encrypt these based upon
    # https://bugzilla.mozilla.org/show_bug.cgi?id=763103
    paypal_id = models.CharField(max_length=255, blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    secret = models.CharField(max_length=255, blank=True, null=True)
    seller = models.OneToOneField(Seller, related_name='paypal')
    # TODO: currencies.

    class Meta:
        db_table = 'seller_paypal'
