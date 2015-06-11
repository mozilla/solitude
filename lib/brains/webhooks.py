import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from lib.brains.models import BraintreeSubscription, BraintreeTransaction
from lib.brains.serializers import serialize_webhook
from lib.transactions import constants
from lib.transactions.models import Transaction
from solitude.base import getLogger

log = getLogger('s.webhooks')


class Processor(object):

    """
    Process a webhook from Braintree.

    Each response contains a different value depending upon the subject.
    """

    def __init__(self, webhook):
        self.webhook = webhook
        # All the transactions found on this webhook.
        self.transactions = []
        # The one transaction that matters for serialization.
        self.transaction = None
        self.processed = False

    def process(self):
        try:
            method = getattr(self, 'process_' + self.webhook.kind)
        except AttributeError:
            log.info('Nothing defined for event: {0}, ignoring.'
                     .format(self.webhook.kind))
            return

        log.info('Processing event: {0}'.format(self.webhook.kind))
        method()
        self.processed = True

    @property
    def data(self):
        if not self.processed:
            return

        if not self.transaction:
            log.info('No transaction, nothing to return.')
            return

        return serialize_webhook(self.webhook, self.transaction)

    def get_transaction(self, status):
        """
        Look through the transactions, finding the most recent transaction
        that matches the transaction. Because transactions are in order
        of the most recent first, finding the first will normally do.
        """
        for transaction in self.transactions:
            if transaction.status == status:
                return transaction

    def process_subscription_charged_successfully(self):
        """
        From the docs:

        Subscription Charged Successfully will be sent if the subscription
        successfully moves to the next billing cycle.

        We have to:
        * find the subscription and create transactions for it.
        * ensure the subscription is set to active.
        """
        subscription = self.get_subscription()
        self.update_subscription(subscription, True)
        self.update_transactions(subscription)
        self.transaction = self.get_transaction(constants.STATUS_CHECKED)

    def process_subscription_cancelled(self):
        """
        We have to:
        * find the subscription and create transactions for it.
        * ensure the subscription is set to inactive.
        """
        subscription = self.get_subscription()
        self.update_subscription(subscription, False)
        self.update_transactions(subscription)

    def update_subscription(self, subscription, active):
        """
        Update the active flag on a subscription, if it already matches
        then nothing happens.
        """
        if subscription.active == active:
            return

        subscription.active = active
        subscription.save()
        log.info('Changed subscription: {} to {}'
                 .format(subscription.pk, 'active' if active else 'inactive'))

    def get_subscription(self):
        """
        From their webhook, get the subscription in the solitude
        database.
        """
        their_subscription = self.webhook.subscription
        try:
            subscription = BraintreeSubscription.objects.get(
                provider_id=their_subscription.id
            )
        except ObjectDoesNotExist:
            log.exception('No subscription found: {}'
                          .format(their_subscription.id))
            raise

        log.info('Found subscription: {}'.format(subscription.pk))
        return subscription

    def update_transactions(self, subscription):
        """
        We are going to make an assumption that there are only
        some transactions that we care about.

        A full list is here: http://bit.ly/1T23ehV

        We are going to record the following:
        * settled
        * failed
        * gateway_rejected
        * processor_declined
        * settlement_declined
        * submitted_for_settlement

        We are going to ignore the following:
        * authorized
        * authorizing
        * authorization_expired
        * settling
        * settlement_pending
        * settlement_confirmed
        * voided

        All of the ignored states are temporary statuses and we don't
        really care about those.

        Transactions on a subscription are:

            Transactions associated with the subscription,
            sorted by creation date with the most recent first.

        The creation time in a transaction is set to the time it was
        created in solitude. Because of lack of millisecond precision on
        data queries, the best way to find the most recent transaction
        is ordering by id.
        """
        their_subscription = self.webhook.subscription
        for their_transaction in their_subscription.transactions:
            status = their_transaction.status
            if status not in settings.BRAINTREE_TRANSACTION_STATUSES:
                log.info('Ignoring transaction status: {}'.format(status))
                continue

            log.info('Processing transaction status: {}'.format(status))
            # These are really the only two end statuses we care about.
            our_status = (
                constants.STATUS_CHECKED if status == 'settled'
                else constants.STATUS_FAILED
            )

            # Write some reason in for the failure.
            reason = ''
            if status == 'processor_declined':
                reason = their_transaction.processor_response_code
            elif status == 'settlement_declined':
                reason = their_transaction.processor_settlement_response_code
            elif status == 'gateway_rejected':
                # There doesn't seem to be a code for gateway rejection.
                reason = their_transaction.gateway_rejection_reason

            reason = (their_transaction.status + ' ' + reason).rstrip()

            try:
                our_transaction = Transaction.objects.get(
                    uid_support=their_transaction.id,
                )
                log.info('Transaction exists: {}'.format(our_transaction.pk))
                # Just a maybe pointless sanity check that the status they are
                # sending in their transaction matches our record.
                if our_transaction.status != our_status:
                    raise ValueError(
                        'Status: {} does not match: {} in transaction: {}'
                        .format(their_transaction.status,
                                our_status,
                                our_transaction.pk))

            except ObjectDoesNotExist:
                our_transaction = Transaction.objects.create(
                    amount=their_transaction.amount,
                    buyer=subscription.paymethod.braintree_buyer.buyer,
                    currency=their_transaction.currency_iso_code,
                    provider=constants.PROVIDER_BRAINTREE,
                    seller=subscription.seller_product.seller,
                    seller_product=subscription.seller_product,
                    status=our_status,
                    status_reason=reason,
                    type=constants.TYPE_PAYMENT,
                    uid_support=their_transaction.id,
                    uuid=str(uuid.uuid4())
                )
                log.info('Transaction created: {}'.format(our_transaction.pk))

                braintree_transaction = BraintreeTransaction.objects.create(
                    transaction=our_transaction,
                    subscription=subscription,
                    paymethod=subscription.paymethod,
                    kind=self.webhook.kind,
                    billing_period_end_date=(
                        their_subscription.billing_period_end_date),
                    billing_period_start_date=(
                        their_subscription.billing_period_start_date),
                    next_billing_date=their_subscription.next_billing_date,
                    next_billing_period_amount=(
                        their_subscription.next_billing_period_amount),
                )
                log.info('BraintreeTransaction created: {}'
                         .format(braintree_transaction.pk))

            self.transactions.append(our_transaction)
