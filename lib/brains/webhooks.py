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
        their_subscription = self.webhook.subscription
        try:
            subscription = BraintreeSubscription.objects.get(
                provider_id=their_subscription.id
            )
        except ObjectDoesNotExist:
            log.exception('No subscription found: {}'
                          .format(their_subscription.id))
            raise

        # Its currently unclear if the most recent transaction is first or
        # last in the last of transactions. Will need to see how multiple
        # transactions look.
        their_transaction = their_subscription.transactions[0]
        transaction = Transaction.objects.create(
            amount=their_transaction.amount,
            buyer=subscription.paymethod.braintree_buyer.buyer,
            currency=their_transaction.currency_iso_code,
            provider=constants.PROVIDER_BRAINTREE,
            seller=subscription.seller_product.seller,
            seller_product=subscription.seller_product,
            status=constants.STATUS_CHECKED,
            type=constants.TYPE_PAYMENT,
            uid_support=their_transaction.id
        )
        log.info('Transaction created: {}'.format(transaction.pk))
