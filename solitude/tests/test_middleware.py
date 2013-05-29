from django.test import TestCase

from nose.tools import eq_
from test_utils import RequestFactory

from solitude.logger import get_oauth_key, get_transaction_id
from solitude.middleware import LoggerMiddleware


class TestMiddleware(TestCase):

    def test_nothing(self):
        req = RequestFactory().get('/')
        LoggerMiddleware().process_request(req)
        eq_(get_oauth_key(), '<anon>')
        eq_(get_transaction_id(), '-')

    def test_something(self):
        req = RequestFactory().get('/', HTTP_TRANSACTION_ID='foo')
        req.OAUTH_KEY = 'bar'
        LoggerMiddleware().process_request(req)
        eq_(get_oauth_key(), 'bar')
        eq_(get_transaction_id(), 'foo')
