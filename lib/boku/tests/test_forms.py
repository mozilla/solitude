from django.forms import ValidationError
from django.test import TestCase

import mock
from nose.tools import assert_raises, eq_, ok_

from lib.boku.errors import BokuException, SignatureError
from lib.boku.forms import (BokuForm, BokuServiceForm,
                            BokuTransactionForm, EventForm)
from lib.boku.tests.utils import (BokuTransactionTest, BokuVerifyServiceTest,
                                  EventTest)
from lib.transactions.constants import PROVIDER_BANGO, STATUS_COMPLETED


class TestBokuForm(TestCase):

    def test_convert(self):
        res = BokuForm(data={'f-': 'b'})
        eq_(res.data, {'f_': 'b'})


class TestForm(EventTest):

    def form_error(self, data, *errors):
        form = EventForm(data)
        assert not form.is_valid()
        eq_(set(errors), set(form.errors.keys()), form.errors)

    def test_action(self):
        form = EventForm(self.sample())
        ok_(form.is_valid(), form.errors)

    def test_wrong_action(self):
        data = self.sample()
        data['action'] = 'foo'
        self.form_error(data, 'action')

    def test_not_exist(self):
        data = self.sample()
        data['param'] = 'does-not-exist'
        self.form_error(data, 'param')

    def test_wrong_provider(self):
        self.trans.provider = PROVIDER_BANGO
        self.trans.save()
        self.form_error(self.sample(), 'param')

    def test_completed(self):
        self.trans.status = STATUS_COMPLETED
        self.trans.save()
        self.form_error(self.sample(), 'param')

    def test_wrong_currency(self):
        data = self.sample()
        data['currency'] = 'FOO'
        self.form_error(data, 'currency', '__all__')

    def test_no_amount(self):
        data = self.sample()
        del data['amount']
        self.form_error(data, 'amount', '__all__')


class BokuTransactionFormTests(BokuTransactionTest):

    def test_callback_url_requires_a_valid_url(self):
        self.post_data['callback_url'] = 'foo'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('callback_url' in form.errors, form.errors)

    def test_forward_url_requires_a_valid_url(self):
        self.post_data['forward_url'] = 'not-a-url'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('forward_url' in form.errors, form.errors)

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

    def test_currency_must_be_valid(self):
        self.post_data['currency'] = 'CDN'
        form = BokuTransactionForm(self.post_data)
        ok_(not form.is_valid(), form.errors)
        ok_('currency' in form.errors)

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


class BokuServiceFormTests(BokuVerifyServiceTest):

    def test_valid_service_id_passes_validation(self):
        form = BokuServiceForm(self.post_data)
        ok_(form.is_valid(), form.errors)

    def test_invalid_service_id_fails_validation(self):
        with mock.patch(
            'lib.boku.client.mocks',
            {'service-prices': (500, '')}
        ):
            form = BokuServiceForm(self.post_data)
            ok_(not form.is_valid(), form.errors)


class TestBokuSignature(EventTest):

    def get_form(self):
        form = EventForm(self.sample())
        form.boku_client = mock.MagicMock()
        return form

    def test_called(self):
        form = self.get_form()
        form.clean_sig()
        assert form.boku_client.check_sig.is_called_with(self.sample)
        assert form.is_valid()

    def test_error(self):
        form = self.get_form()
        form.boku_client.check_sig.side_effect = SignatureError('sig error')
        with self.assertRaises(ValidationError):
            form.clean_sig()
