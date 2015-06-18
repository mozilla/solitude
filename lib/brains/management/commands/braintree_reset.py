from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from lib.brains.models import BraintreePaymentMethod, BraintreeSubscription
from lib.transactions.models import Transaction


class Command(BaseCommand):
    help = 'Clean up braintree related data for development.'
    option_list = BaseCommand.option_list + (
        make_option(
            '--clear-subscriptions', action='store_true',
            dest='clear_subscriptions',
            help='Remove all subscription data'
        ),
        make_option(
            '--clear-transactions', action='store_true',
            dest='clear_transactions',
            help='Remove all transaction data'
        ),
        make_option(
            '--clear-paymethods', action='store_true',
            dest='clear_paymethods',
            help=('Remove all saved payment methods. This also removes data '
                  'tied to the payment methods.')
        ),
    )

    def handle(self, *args, **options):
        did_something = False

        if options['clear_subscriptions']:
            did_something = True
            self._clear(BraintreeSubscription)
        if options['clear_paymethods']:
            did_something = True
            self._clear(BraintreePaymentMethod)
        if options['clear_transactions']:
            did_something = True
            self._clear(Transaction)

        if not did_something:
            raise CommandError('Nothing to do. Try specifying some options.')

    def _clear(self, model):
        count = model.objects.count()
        model.objects.all().delete()
        print '{} objects deleted: {}'.format(model.__name__, count)
