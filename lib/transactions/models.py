from django.db import models
from django.dispatch import receiver

from .constants import (STATUS_DEFAULT, STATUSES,
                        TYPE_DEFAULT, TYPES, TYPE_PAYMENT)
from lib.paypal.signals import create
from lib.paypal.resources.pay import PayResource


class PaypalTransaction(models.Model):
    # This is our tracking id.
    uuid = models.CharField(max_length=255, db_index=True, unique=True)
    seller = models.ForeignKey('sellers.SellerPaypal')
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    # This is needed for refunds.
    pay_key = models.CharField(max_length=255, db_index=True, unique=True)
    # This is PayPals tracking id.
    correlation_id = models.CharField(max_length=255, db_index=True,
                                      unique=True)
    type = models.PositiveIntegerField(default=TYPE_DEFAULT,
                                       choices=sorted(TYPES.items()))
    status = models.PositiveIntegerField(default=STATUS_DEFAULT,
                                         choices=sorted(STATUSES.items()))

    class Meta:
        db_table = 'transaction_paypal'


@receiver(create, dispatch_uid='transaction-create')
def create_transaction(sender, **kwargs):
    if not isinstance(sender, PayResource):
        return

    data = kwargs['bundle'].data
    clean = kwargs['form']
    PaypalTransaction.objects.create(
            type=TYPE_PAYMENT, correlation_id=data['correlation_id'],
            pay_key=data['pay_key'], seller=clean['seller'].paypal,
            amount=clean['amount'], currency=clean['currency'],
            uuid=data['uuid'])
