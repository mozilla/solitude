from decimal import Decimal

from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_, raises

from lib.boku.client import BokuException
from lib.boku.tests.utils import EventTest
from lib.transactions.constants import STATUS_COMPLETED


class TestEvent(EventTest):

    def setUp(self):
        super(TestEvent, self).setUp()
        self.url = reverse('event-list')

    def test_get(self):
        eq_(self.client.get(self.url).status_code, 405)

    def test_fail(self):
        bad = {'foo': 'bar'}
        eq_(self.client.post(self.url, data=bad).status_code, 400)

    def test_good(self):
        self.add_seller_boku()
        eq_(self.client.post(self.url, data=self.sample()).status_code, 200)
        self.trans = self.trans.reget()

        eq_(self.trans.status, STATUS_COMPLETED)
        eq_(self.trans.amount, Decimal('1.00'))
        eq_(self.trans.currency, 'MXN')
        eq_(self.trans.uid_support, 'some:trxid')

    @raises(BokuException)
    @patch('lib.boku.client.mocks', {'verify-trx-id': (500, '')})
    def test_verify_fails(self):
        self.add_seller_boku()
        eq_(self.client.post(self.url, data=self.sample()).status_code, 200)
