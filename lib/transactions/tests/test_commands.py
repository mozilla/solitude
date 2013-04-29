import csv
from datetime import datetime
from tempfile import NamedTemporaryFile
from unittest import TestCase

from nose.tools import eq_

from lib.transactions.models import Transaction
from lib.transactions.management.commands.stats_log import generate_log
from lib.sellers.tests.utils import make_seller_paypal


class TestLog(TestCase):

    def test_filter(self):
        seller, paypal, product = make_seller_paypal('some:other:uuid')
        self.first = Transaction.objects.create(provider=1,
            seller_product=product, uuid='uuid')
        name = NamedTemporaryFile().name
        generate_log(datetime.today(), name)
        with open(name, 'rb') as csvfile:
            output = csv.reader(csvfile)
            eq_(next(output)[0], 'version')
            eq_(next(output)[1], 'uuid')
