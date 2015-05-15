from django import test
from django.db import transaction

from nose.tools import eq_, ok_
from slumber.exceptions import HttpClientError

from curling import lib
from solitude.exceptions import custom_exception_handler
from solitude.tests.live import LiveTestCase


class TestErrors(LiveTestCase):

    def test_not_found(self):
        with self.assertRaises(HttpClientError) as error:
            self.request.by_url('/this/does-not-exist/').get()
        eq_(error.exception.response.json, {})

    def test_403_html(self):
        with self.assertRaises(HttpClientError) as error:
            lib.API(self.live_server_url).by_url('/this/does-not-exist/').get()
        eq_(error.exception.response.json, {})

    def test_drf_403_html(self):
        with self.assertRaises(HttpClientError) as error:
            lib.API(self.live_server_url).by_url('/generic/transaction/').get()
        eq_(error.exception.response.json,
            {'detail': 'Incorrect authentication credentials.'})


class TestRollback(test.TestCase):
    def test_did_rollback(self):
        custom_exception_handler(Exception())
        ok_(transaction.get_connection().get_rollback())
