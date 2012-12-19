from django.db import models
from django.dispatch import receiver

import commonware.log

from lib.bango.signals import create as bango_create
from lib.paypal.signals import create as paypal_create
from lib.transactions import constants

from solitude.base import get_object_or_404, Model

log = commonware.log.getLogger('s.transaction')


class Transaction(Model):
    # In the case of some transactions (e.g. Bango) we don't know the amount
    # until the transaction reaches a certain stage.
    amount = models.DecimalField(max_digits=9, decimal_places=2, blank=True,
                                 null=True)
    buyer = models.ForeignKey('buyers.Buyer', blank=True, null=True,
                              db_index=True)
    currency = models.CharField(max_length=3, default='USD')
    provider = models.PositiveIntegerField(
                              choices=constants.SOURCES_CHOICES)
    related = models.ForeignKey('self', blank=True, null=True,
                              on_delete=models.PROTECT)
    seller_product = models.ForeignKey('sellers.SellerProduct', db_index=True)
    status = models.PositiveIntegerField(default=constants.STATUS_DEFAULT,
                              choices=constants.STATUSES_CHOICES)
    source = models.CharField(max_length=255, blank=True, null=True,
                              db_index=True)
    type = models.PositiveIntegerField(default=constants.TYPE_DEFAULT,
                              choices=constants.TYPES_CHOICES)
    # Lots of IDs.
    # An ID from the provider that can be used for support on this specific
    # transaction. Optional.
    uid_support = models.CharField(max_length=255, db_index=True, blank=True,
                                   null=True)
    # An ID from the provider that relates to this transaction.
    uid_pay = models.CharField(max_length=255, db_index=True)
    # An ID we generate for this transaction.
    uuid = models.CharField(max_length=255, db_index=True, unique=True)

    class Meta(Model.Meta):
        db_table = 'transaction'
        ordering = ('-id',)
        unique_together = (('uid_pay', 'provider'),
                           ('uid_support', 'provider'))

    @classmethod
    def create(cls, **kw):
        """
        Use model validation to make sure when transactions get created,
        we do a full clean and get the correct uid conflicts sorted out.
        """
        transaction = cls(**kw)
        transaction.full_clean()
        transaction.save()
        return transaction


@receiver(paypal_create, dispatch_uid='transaction-create-paypal')
def create_paypal_transaction(sender, **kwargs):
    if sender.__class__._meta.resource_name != 'pay':
        return

    data = kwargs['bundle'].data
    clean = kwargs['form']

    transaction = Transaction.create(
            amount=clean['amount'],
            currency=clean['currency'],
            provider=constants.SOURCE_PAYPAL,
            seller_product=clean['seller_product'],
            source=clean.get('source', ''),
            type=constants.TYPE_PAYMENT,
            uid_pay=data['pay_key'],
            uid_support=data['correlation_id'],
            uuid=data['uuid'])
    log.info('Transaction: %s, paypal status: %s'
             % (transaction.pk, data['status']))


@receiver(paypal_create, dispatch_uid='transaction-complete-paypal')
def completed_paypal_transaction(sender, **kwargs):
    if sender.__class__._meta.resource_name != 'pay-check':
        return

    data = kwargs['bundle'].data
    transaction = get_object_or_404(Transaction, uid_pay=data['pay_key'])

    if transaction.status == constants.STATUS_PENDING:
        log.info('Transaction: %s, paypal status: %s'
                 % (transaction.pk, data['status']))
        if data['status'] == 'COMPLETED':
            transaction.status = constants.STATUS_CHECKED
            transaction.save()


@receiver(bango_create, dispatch_uid='transaction-create-bango')
def create_bango_transaction(sender, **kwargs):
    if sender.__class__._meta.resource_name != 'billing':
        return

    # Pull information from all the over the place.
    bundle = kwargs['bundle'].data
    data = kwargs['data']
    form = kwargs['form']
    seller_product = form.cleaned_data['seller_product_bango'].seller_product

    transaction = Transaction.create(
            provider=constants.SOURCE_BANGO,
            seller_product=seller_product,
            source=data.get('source', ''),
            type=constants.TYPE_PAYMENT,
            uuid=data['externalTransactionId'],
            uid_pay=bundle['billingConfigurationId'])

    log.info('Bango transaction: %s pending' % (transaction.pk,))
