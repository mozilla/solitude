from decimal import Decimal

from django.core.urlresolvers import reverse

from mock import patch
from nose.tools import eq_, raises

from lib.boku.client import BokuException
from lib.boku.tests.utils import EventTest
from lib.transactions.constants import (
    STATUS_CANCELLED, STATUS_COMPLETED, STATUS_FAILED)


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

    @patch('lib.boku.client.BokuClient.api_call')
    def test_trans_failure_from_error_code(self, api):
        api.side_effect = BokuException(
            'boku failure',
            result_code=5, result_msg='Failed - external billing failure')
        eq_(self.client.post(self.url, data=self.sample()).status_code, 200)
        self.trans = self.trans.reget()
        eq_(self.trans.status, STATUS_FAILED)

    @patch('lib.boku.client.BokuClient.api_call')
    def test_cancelled_trans_from_error_code(self, api):
        api.side_effect = BokuException(
            'cancelled purchase', result_code=8, result_msg='cancellation')
        eq_(self.client.post(self.url, data=self.sample()).status_code, 200)
        self.trans = self.trans.reget()
        eq_(self.trans.status, STATUS_CANCELLED)

    @raises(BokuException)
    @patch('lib.boku.client.BokuClient.api_call')
    def test_unknown_boku_error(self, api):
        api.side_effect = BokuException(
            'boku explosion', result_code=-1, result_msg='unknown error')
        self.client.post(self.url, data=self.sample())
