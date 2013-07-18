from datetime import date, timedelta
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from lib.bango.models import Status


class Command(BaseCommand):
    help = 'Deletes all statuses with a lifetime greater than the parameter.'
    option_list = BaseCommand.option_list + (
        make_option(
            '--lifetime',
            action='store_true',
            dest='lifetime',
            default=settings.BANGO_STATUSES_LIFETIME,
            help=('Set the maximum lifetime in days of cleaned statuses. '
                  'Default: %s (BANGO_STATUSES_LIFETIME setting)'
                  % settings.BANGO_STATUSES_LIFETIME)
        ),
    )

    def handle(self, *args, **options):
        boundary_date = date.today() - timedelta(days=options['lifetime'])
        Status.objects.filter(created__lte=boundary_date).delete()
