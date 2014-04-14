import mock
from nose.tools import assert_raises, eq_, ok_
from test_utils import TestCase

from lib.boku.errors import BokuException
from lib.boku.forms import BokuForm, BokuTransactionForm, EventForm
from lib.boku.tests.utils import BokuTransactionTest, EventTest
from lib.transactions.constants import PROVIDER_BANGO, STATUS_COMPLETED


class TestBokuForm(TestCase):

    def test_convert(self):
        res = BokuForm(data={'f-': 'b'})
        eq_(res.data, {'f_': 'b'})


class TestForm(EventTest):

    def test_action(self):
        form = EventForm(self.sample())
        ok_(form.is_valid(), form.errors)

    def test_wrong_action(self):
        data = self.sample()
        data['action'] = 'foo'
        form = EventForm(data)
        ok_(not form.is_valid(), form.errors)

    def test_not_exist(self):
        data = self.sample()
        data['param'] = 'does-not-exist'
        form = EventForm(data)
        ok_(not form.is_valid(), form.errors)

    def test_wrong_provider(self):
        self.trans.provider = PROVIDER_BANGO
        self.trans.save()
        ok_(not EventForm(self.sample()).is_valid())

    def test_completed(self):
        self.trans.status = STATUS_COMPLETED
        self.trans.save()
        ok_(not EventForm(self.sample()).is_valid())


class BokuTransactionFormTests(BokuTransactionTest):

    def test_callback_url_requires_a_valid_url(self):
        self.post_data['callback_url'] = 'foo'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('callback_url' in form.errors, form.errors)

    def test_country_requires_a_defined_country_code(self):
        self.post_data['country'] = 'foo'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('country' in form.errors)

    def test_price_requires_a_decimal_value(self):
        self.post_data['price'] = 'foo'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('price' in form.errors)

    def test_price_requires_an_existing_boku_price_tier(self):
        self.post_data['price'] = '1.00'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_(form.ERROR_BAD_PRICE in form.errors['__all__'])

    def test_seller_uuid_requires_an_existing_seller(self):
        self.post_data['seller_uuid'] = 'foo'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('seller_uuid' in form.errors)

    def test_seller_uuid_requires_a_boku_seller(self):
        self.seller_boku.delete()
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('seller_uuid' in form.errors)

    def test_starting_a_transaction_before_validation_fails(self):
        form = BokuTransactionForm(self.post_data)
        assert_raises(Exception, form.start_transaction)

    def test_boku_failure_raises_BokuException(self):
        form = BokuTransactionForm(self.post_data)
        ok_(form.is_valid(), form.errors)

        with mock.patch('lib.boku.client.mocks', {'prepare': (500, '')}):
            assert_raises(BokuException, form.start_transaction)

    def test_start_boku_transaction_with_valid_data(self):
        form = BokuTransactionForm(self.post_data)
        ok_(form.is_valid(), form.errors)

        transaction = form.start_transaction()
        ok_('transaction_id' in transaction, transaction)
        ok_('buy_url' in transaction, transaction)
