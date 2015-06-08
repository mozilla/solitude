from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from lib.brains.models import BraintreeSubscription
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

    def process(self):
        try:
            method = getattr(self, 'process_' + self.webhook.kind)
        except AttributeError:
            log.info('Nothing defined for event: {0}, ignoring.'
                     .format(self.webhook.kind))
            return

        log.info('Processing event: {0}'.format(self.webhook.kind))
        method()

    def process_subscription_charged_successfully(self):
        """
        From the docs:

        Subscription Charged Successfully will be sent if the subscription
        successfully moves to the next billing cycle.

        We have to:
        * find the subscription and create a transaction for it.
        """
        subscription = self.get_subscription()
        self.update_transactions(self.webhook.subscription, subscription)

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

    def update_transactions(self, their_subscription, subscription):
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

        We are going to ignore the following:
        * authorized
        * authorizing
        * authorization_expired
        * settling
        * settlement_pending
        * settlement_confirmed
        * submitted_for_settlement
        * voided

        All of the ignored states are temporary statuses and we don't
        really care about those.
        """
        for their_transaction in their_subscription.transactions:
            status = their_transaction.status
            if status not in settings.BRAINTREE_TRANSACTION_STATUSES:
                log.info('Ignoring transaction status: {}'.format(status))
                continue

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
                    uid_support=their_transaction.id
                )
                log.info('Transaction created: {}'.format(our_transaction.pk))
