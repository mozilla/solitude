from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import RequestFactory

from mock import ANY, patch

from lib.transactions import constants
from lib.transactions.forms import check_status, UpdateForm
from solitude.base import APITest


@patch.object(settings, 'TRANSACTION_LOCKDOWN', 60)
class TestForm(APITest):

    def setUp(self):
        super(TestForm, self).setUp()
        self.req = RequestFactory().get('/')

    @patch.object(settings, 'TRANSACTION_LOCKDOWN', 60)
    def test_lockdown(self):
        check_status({'created': datetime.now() - timedelta(seconds=55),
                      'status': constants.STATUS_CHECKED,
                      'provider': constants.PROVIDER_BANGO,
                      'seller_product': 1},
                     {'status': constants.STATUS_COMPLETED})
        with self.assertRaises(ValidationError):
            check_status({'created': datetime.now() - timedelta(seconds=65),
                          'status': constants.STATUS_CHECKED},
                         {})

    def test_failed(self):
        with self.assertRaises(ValidationError):
            check_status({'created': datetime.now(), 'status':
                          constants.STATUS_FAILED},
                         {'status': constants.STATUS_PENDING})

    def test_checked(self):
        with self.assertRaises(ValidationError):
            check_status({'created': datetime.now(),
                          'status': constants.STATUS_CHECKED,
                          'provider': constants.PROVIDER_BANGO,
                          'seller_product': 1},
                         {'status': constants.STATUS_PENDING})
        check_status({'created': datetime.now(),
                      'status': constants.STATUS_CHECKED,
                      'provider': constants.PROVIDER_BANGO,
                      'seller_product': 1},
                     {'status': constants.STATUS_COMPLETED})

    def test_errored_ok(self):
        check_status({'created': datetime.now(),
                      'status': constants.STATUS_STARTED},
                     {'status': constants.STATUS_ERRORED})

    def test_completed_not_ok(self):
        with self.assertRaises(ValidationError):
            check_status({'created': datetime.now(),
                          'status': constants.STATUS_STARTED},
                         {'status': constants.STATUS_COMPLETED})

    def test_seller_product_needed(self):
        with self.assertRaises(ValidationError):
            check_status({'status': constants.STATUS_STARTED,
                          'provider': constants.PROVIDER_BOKU,
                          'created': datetime.now()},
                         {'status': constants.STATUS_COMPLETED})

    def test_provide_set_twice(self):
        form = UpdateForm(
            {'status': constants.STATUS_CHECKED,
             'provider': constants.PROVIDER_BOKU},
            original_data={
                'created': datetime.now(),
                'status': constants.STATUS_COMPLETED,
                'provider': constants.PROVIDER_BANGO,
                'seller_product': 1,
                },
            request=self.req)
        assert not form.is_valid()

    @patch('solitude.base._log_cef')
    def test_cef_ok(self, _log_cef):
        form = UpdateForm(
            {'status': constants.STATUS_CHECKED},
            original_data={
                'created': datetime.now(),
                'status': constants.STATUS_COMPLETED,
                'provider': constants.PROVIDER_BANGO,
                'seller_product': 1,
                },
            request=self.req)
        assert form.is_valid(), form.errors
        _log_cef.assert_called_with(
            'Transaction change success', 5, ANY,
            msg='Transaction change success', config=ANY, signature=ANY,
            cs7Label='new', cs6Label='old', cs6='completed', cs7='checked'
        )

    @patch('solitude.base._log_cef')
    def test_cef_failed(self, _log_cef):
        form = UpdateForm(
            {'status': constants.STATUS_PENDING},
            original_data={
                'created': datetime.now(),
                'status': constants.STATUS_CANCELLED},
            request=self.req)
        assert not form.is_valid()
        _log_cef.assert_called_with(
            'Transaction change failure', 7, ANY,
            msg='Transaction change failure', config=ANY, signature=ANY,
            cs7Label='new', cs6Label='old', cs6='cancelled', cs7='pending')

    @patch('solitude.base._log_cef')
    def test_cef_not(self, _log_cef):
        form = UpdateForm(
            {'status': constants.STATUS_PENDING},
            original_data={
                'created': datetime.now(),
                'status': constants.STATUS_PENDING},
            request=self.req)
        assert form.is_valid()
        assert not _log_cef.called
