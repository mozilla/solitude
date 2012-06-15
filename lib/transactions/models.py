from django.db import models
from django.dispatch import receiver

import commonware.log

from lib.transactions import constants
from lib.paypal.signals import create

log = commonware.log.getLogger('s.transaction')


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
    type = models.PositiveIntegerField(default=constants.TYPE_DEFAULT,
                                    choices=sorted(constants.TYPES.items()))
    status = models.PositiveIntegerField(default=constants.STATUS_DEFAULT,
                                    choices=sorted(constants.STATUSES.items()))

    class Meta:
        db_table = 'transaction_paypal'


@receiver(create, dispatch_uid='transaction-create')
def create_pending_transaction(sender, **kwargs):
    if sender.__class__._meta.resource_name != 'pay':
        return

    data = kwargs['bundle'].data
    clean = kwargs['form']

    transaction = PaypalTransaction.objects.create(
            type=constants.TYPE_PAYMENT, correlation_id=data['correlation_id'],
            pay_key=data['pay_key'], seller=clean['seller'].paypal,
            amount=clean['amount'], currency=clean['currency'],
            uuid=data['uuid'])
    log.info('Transaction: %s, paypal status: %s'
             % (transaction.pk, data['status']))


@receiver(create, dispatch_uid='transaction-complete')
def note_completed_transaction(sender, **kwargs):
    if sender.__class__._meta.resource_name != 'pay-check':
        return

    data = kwargs['bundle'].data
    transaction = sender.get_object_or_404(PaypalTransaction,
                                           pay_key=data['pay_key'])

    if transaction.status == constants.STATUS_PENDING:
        log.info('Transaction: %s, paypal status: %s'
                 % (transaction.pk, data['status']))
        if data['status'] == 'COMPLETED':
            transaction.status = constants.STATUS_COMPLETED
            transaction.save()
