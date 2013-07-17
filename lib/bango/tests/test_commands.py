from datetime import date, timedelta

from django.core.management import call_command

from nose.tools import eq_

import test_utils
import utils
from lib.bango.models import Status


class TestCleanStatusesCommand(test_utils.TestCase):

    def setUp(self):
        """
        Generates 3 statuses with different lifetimes of 5, 20 and 35 days
        to test both default and custom `lifetime` parameter.
        """
        sellers = utils.make_sellers()
        for i in (5, 20, 35):
            status = Status.objects.create(
                seller_product_bango=sellers.product_bango,
            )
            # Work around due to the `auto_now_add` option
            status.created = date.today() - timedelta(days=i)
            status.save()

    def test_command_call(self):
        with self.settings(BANGO_STATUSES_LIFETIME=30):
            call_command('clean_statuses')
            eq_(Status.objects.all().count(), 2)

    def test_lifetime_parameter(self):
        call_command('clean_statuses', **{'lifetime': 10})
        eq_(Status.objects.all().count(), 1)
