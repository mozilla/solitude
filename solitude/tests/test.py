import json

from nose.tools import eq_
import test_utils

from lib.paypal.errors import PaypalError
from solitude.base import Resource


class TestError(test_utils.TestCase):

    def setUp(self):
        self.request = test_utils.RequestFactory().get('/')
        self.resource = Resource()

    def test_error(self):
        try:
            1/0
        except Exception as error:
            res = self.resource._handle_500(self.request, error)

        data = json.loads(res.content)
        eq_(data['error_code'], '')
        eq_(data['error_message'], 'integer division or modulo by zero')

    def test_paypal_error(self):
        try:
            raise PaypalError(id=520003, message='wat?')
        except Exception as error:
            res = self.resource._handle_500(self.request, error)

        data = json.loads(res.content)
        eq_(data['error_code'], '520003')
        eq_(data['error_message'], 'wat?')
