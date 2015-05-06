from nose.tools import eq_
from slumber.exceptions import HttpClientError

from curling import lib
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
