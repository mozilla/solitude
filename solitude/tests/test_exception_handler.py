from django.test import TestCase

import mock
from nose.tools import eq_

from lib.bango.errors import BangoImmediateError
from lib.brains.errors import BraintreeResultError
from solitude.exceptions import custom_exception_handler


@mock.patch('solitude.exceptions.rollback')
class TestExceptionHandler(TestCase):

    def test_braintree(self, rollback):
        res = custom_exception_handler(BraintreeResultError(mock.MagicMock()))
        eq_(res.status_code, 400)
        assert rollback.called

    def test_bango(self, rollback):
        res = custom_exception_handler(BangoImmediateError('test'))
        eq_(res.status_code, 400)
        assert rollback.called
