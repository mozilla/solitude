from django.db import models
from django.dispatch import receiver

from django_statsd.clients import statsd

from lib.bango.signals import create as bango_create
from lib.paypal.signals import create as paypal_create
from lib.transactions import constants

from solitude.base import get_object_or_404, Model
from solitude.logger import getLogger

log = getLogger('s.transaction')
stats_log = getLogger('s.transaction.stats')


class Transaction(Model):
    # In the case of some transactions (e.g. Bango) we don't know the amount
    # until the transaction reaches a certain stage.
    amount = models.DecimalField(max_digits=9, decimal_places=2, blank=True,
                                 null=True)
    buyer = models.ForeignKey('buyers.Buyer', blank=True, null=True,
                              db_index=True)
    # The carrier if this was carrier billing.
    carrier = models.CharField(max_length=255, blank=True, null=True,
                               db_index=True)
    currency = models.CharField(max_length=3, blank=True)
    provider = models.PositiveIntegerField(choices=constants.PROVIDERS_CHOICES)
    # The region of the purchase.
    region = models.CharField(max_length=255, blank=True, null=True,
                              db_index=True)
    related = models.ForeignKey('self', blank=True, null=True,
                                on_delete=models.PROTECT,
                                related_name='relations')
    seller_product = models.ForeignKey('sellers.SellerProduct', db_index=True)
    seller = models.ForeignKey('sellers.Seller', db_index=True,
                               blank=True, null=True)
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
    uid_pay = models.CharField(max_length=255, db_index=True, blank=True,
                               null=True)
    # Absolute payment start URL for this transaction.
    pay_url = models.CharField(max_length=255, blank=True, null=True)
    # An ID we generate for this transaction, we'll generate one for you if
    # you don't specify one.
    uuid = models.CharField(max_length=255, db_index=True, unique=True)

    # A general "store whatever you like" field. Solitude wont use this.
    notes = models.TextField(blank=True, null=True)

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

    def is_refunded(self):
        return Transaction.objects.filter(
            related=self,
            type__in=constants.TYPE_REFUNDS_REVERSALS,
            status=constants.STATUS_COMPLETED).exists()

    def for_log(self):
        return (
            'v4',  # Version.
            self.uuid,
            self.created.isoformat(),
            self.modified.isoformat(),
            self.amount,
            self.currency,
            self.status,
            self.buyer.uuid if self.buyer else None,
            self.seller_product.seller.uuid,
            self.source,
            self.carrier,
            self.region,
            self.provider)


@receiver(paypal_create, dispatch_uid='transaction-create-paypal')
def create_paypal_transaction(sender, **kwargs):
    if sender.__class__._meta.resource_name != 'pay':
        return

    data = kwargs['bundle'].data
    clean = kwargs['form']

    transaction = Transaction.create(
        amount=clean['amount'],
        currency=clean['currency'],
        provider=constants.PROVIDER_PAYPAL,
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

    transaction, c = Transaction.objects.safer_get_or_create(
        uuid=data['transaction_uuid'],
        status=constants.STATUS_RECEIVED,
        provider=constants.PROVIDER_BANGO,
        seller_product=seller_product)

    transaction.source = form.cleaned_data.get('source', '')
    transaction.carrier = form.cleaned_data.get('carrier', '')
    transaction.region = form.cleaned_data.get('region', '')
    # uid_support will be set with the transaction id.
    # uid_pay is the uid of the billingConfiguration request.
    if 'billingConfigurationId' in bundle:
        # Transactions that fail to create this will not have this.
        transaction.uid_pay = bundle['billingConfigurationId']
    transaction.status = kwargs.get('status', constants.STATUS_PENDING)
    transaction.type = constants.TYPE_PAYMENT
    transaction.save()

    # This shows up in syslog:
    log.info('Bango transaction: %s pending' % (transaction.pk,))
    # This does not! FIXME. bug 888075
    log.info('Created trans from Bango %s, uuid %s; pending'
             % (transaction.pk, transaction.uuid))
    statsd.incr('solitude.pending_transactions')


@receiver(models.signals.post_save, dispatch_uid='time_status_change',
          sender=Transaction)
def time_status_change(sender, **kwargs):
    # There's no status change if the transaction was just created.
    if kwargs.get('raw', False) or kwargs.get('created', False):
        return

    obj = kwargs['instance']
    status = constants.STATUSES_INVERTED[obj.status]
    statsd.timing('transaction.status.{0}'.format(status),
                  (obj.modified - obj.created).seconds)


class TransactionLog(Model):
    transaction = models.ForeignKey(Transaction, related_name='log')
    type = models.IntegerField(choices=constants.LOG_CHOICES)

    class Meta(Model.Meta):
        db_table = 'transaction_log'
