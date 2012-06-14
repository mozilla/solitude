from django.db import models

from .constants import STATUS_DEFAULT, STATUSES, TYPE_DEFAULT, TYPES


class PaypalTransaction(models.Model):
    uuid = models.CharField(max_length=255, db_index=True)
    seller = models.CharField('BuyerPaypal')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    pay_key = models.CharField(max_length=255, db_index=True)
    correlation_id = models.CharField(max_length=255, db_index=True)
    type = models.PositiveIntegerField(default=TYPE_DEFAULT,
                                       choices=sorted(TYPES.items()))
    status = models.PositiveIntegerField(default=STATUS_DEFAULT,
                                         choices=sorted(STATUSES.items()))

    class Meta:
        db_table = 'transaction_paypal'
