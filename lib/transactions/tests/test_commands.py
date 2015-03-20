import csv
from datetime import datetime
from tempfile import NamedTemporaryFile

from django import test

from nose.tools import eq_, raises

from lib.sellers.models import Seller, SellerProduct
from lib.transactions import constants
from lib.transactions.management.commands.log import generate_log
from lib.transactions.models import Transaction


class TestLog(test.TestCase):

    def setUp(self):
        self.name = NamedTemporaryFile().name
        seller = Seller.objects.create(uuid='uuid')
        self.product = SellerProduct.objects.create(seller=seller,
                                                    external_id='xyz')
        self.first = Transaction.objects.create(
            provider=1,
            seller_product=self.product, uuid='uuid')

    def results(self):
        return csv.reader(open(self.name, 'rb'))

    def test_filter(self):
        generate_log(datetime.today(), self.name, 'stats')
        output = self.results()
        eq_(next(output)[0], 'version')
        eq_(next(output)[1], 'uuid')

    @raises(StopIteration)
    def test_stats_log_stops(self):
        generate_log(datetime.today(), self.name, 'revenue')
        output = self.results()
        eq_(next(output)[0], 'version')
        next(output)  # There is no line 1, transaction not written.

    def test_stats_log(self):
        self.first.status = constants.STATUS_CHECKED
        self.first.save()

        generate_log(datetime.today(), self.name, 'revenue')
        output = self.results()
        eq_(next(output)[0], 'version')
        eq_(next(output)[1], 'uuid')

    @raises(StopIteration)
    def test_multiple(self):
        self.first.status = constants.STATUS_CHECKED
        self.first.log.create(type=constants.LOG_REVENUE)
        self.first.save()

        generate_log(datetime.today(), self.name, 'revenue')
        output = self.results()
        eq_(next(output)[0], 'version')
        next(output)  # There is no line 1, transaction not written.

    def test_other(self):
        self.first.status = constants.STATUS_CHECKED
        self.first.log.create(type=constants.LOG_STATS)
        self.first.save()

        generate_log(datetime.today(), self.name, 'revenue')
        output = self.results()
        eq_(next(output)[0], 'version')
        eq_(next(output)[1], 'uuid')
