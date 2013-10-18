import csv
import os
import tempfile
from datetime import datetime, timedelta
from optparse import make_option

from lib.transactions import constants
from lib.transactions.models import Transaction
from solitude.logger import getLogger
from solitude.management.commands.push_s3 import push

from django.core.management.base import BaseCommand, CommandError

log = getLogger('s.transactions')


def generate_log(day, filename, log_type):
    out = open(filename, 'w')
    writer = csv.writer(out)
    next_day = day + timedelta(days=1)
    writer.writerow(('version', 'uuid', 'created', 'modified', 'amount',
                     'currency', 'status', 'buyer', 'seller', 'source',
                     'carrier', 'region'))

    transactions = Transaction.objects.filter(modified__range=(day, next_day))

    if log_type == 'stats':
        for row in transactions:
            row.log.get_or_create(type=constants.LOG_STATS)
            writer.writerow(row.for_log())

    if log_type == 'revenue':
        transactions = (transactions
            .filter(status__in=(constants.STATUS_COMPLETED,
                                constants.STATUS_CHECKED))
            .exclude(log__type=constants.LOG_REVENUE))

        for row in transactions:
            obj, created = row.log.get_or_create(type=constants.LOG_REVENUE)
            if not created:
                # This should never happen, but just in case.
                print 'Transaction skipped: {0}'.format(row.uuid)
                continue

            writer.writerow(row.for_log())


class Command(BaseCommand):
    """
    Generate a stats log in CSV format, then uploads it to S3.

    :param date: date to process (defaults to yesterday).
    :param dir: directory file will be written to (defaults to temp).

    If there is no directory specified a temporary directory is used and
    the file removed afterwards.
    """
    option_list = BaseCommand.option_list + (
        make_option('--date', action='store', type='string', dest='date'),
        make_option('--dir', action='store', type='string', dest='dir'),
        make_option('--type', action='store', type='string', dest='log_type'),
        make_option('--today', action='store_const', const=True, dest='today')
    )

    types = ['stats', 'revenue']

    def handle(self, *args, **options):
        log_type = options['log_type']
        if log_type not in self.types:
            msg = 'Type not valid, must be one of: %s' % self.types
            log.debug(msg)
            raise CommandError(msg)

        dir_ = not options['dir']
        if dir_:
            log.debug('No directory specified, making temp.')
            dir_ = tempfile.mkdtemp()

        # Default to yesterday for backwards compat.
        day = (datetime.today() if options['today']
               else datetime.today() - timedelta(days=1))

        date = (datetime.strptime(options['date'], '%Y-%m-%d')
                if options['date'] else day).date()
        filename = os.path.join(dir_, '{0}.{1}.log'.format(
            date.strftime('%Y-%m-%d'), log_type))

        generate_log(date, filename, log_type)
        log.debug('Log generated to: %s', filename)
        push(filename)
        if not options['dir']:
            log.debug('No directory specified, cleaning log after upload.')
            os.remove(filename)
