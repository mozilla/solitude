import csv
from datetime import datetime, timedelta
from optparse import make_option
from os.path import join


from lib.transactions.models import Transaction
from solitude.management.commands.push_s3 import push

from django.core.management.base import BaseCommand


def generate_log(day, filename):
    out = open(filename, 'w')
    writer = csv.writer(out)
    next_day = day + timedelta(days=1)
    writer.writerow(('version', 'uuid', 'created', 'modified', 'amount',
                     'currency', 'status', 'buyer', 'seller'))
    transactions = Transaction.objects.filter(modified__range=(day, next_day))
    for transaction in transactions:
        writer.writerow(transaction.for_log())


class Command(BaseCommand):
    """
    Generate a stats log in CSV format.

    :param date: date to process (defaults to yesterday).
    :param dir: directory file will be written to (defaults to current).
    """
    option_list = BaseCommand.option_list + (
        make_option('--date', action='store', type='string', dest='date'),
        make_option('--dir', action='store', type='string', dest='dir'),
    )

    def handle(self, *args, **options):
        yesterday = datetime.today() - timedelta(days=1)
        date = (datetime.strptime(options['date'], '%Y-%m-%d')
                if options['date'] else yesterday).date()
        filename = join(options['dir'] if options['dir'] else '.',
                        date.strftime('%Y-%m-%d') + '.log')
        generate_log(date, filename)
        push(filename)
