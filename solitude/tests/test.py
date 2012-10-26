import json

import mock
from nose.tools import eq_
from tastypie.exceptions import ImmediateHttpResponse
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


class TestBase(test_utils.TestCase):

    def setUp(self):
        self.request = test_utils.RequestFactory().get('/')
        self.resource = Resource()

    @mock.patch('solitude.base.log_cef')
    def test_cef(self, log_cef):
        self.resource.method_check = mock.Mock()
        with self.assertRaises(ImmediateHttpResponse):
            self.resource.dispatch('POST', self.request, api_name='foo',
                                   resource_name='bar')
        args = log_cef.call_args[0]
        eq_(args[0], 'foo:bar')
        kw = log_cef.call_args[1]
        eq_(kw['msg'], 'foo:bar')
        eq_(kw['config']['cef.product'], 'Solitude')

    @mock.patch('solitude.base.log_cef')
    def test_unknowncef(self, log_cef):
        self.resource.method_check = mock.Mock()
        with self.assertRaises(ImmediateHttpResponse):
            self.resource.dispatch('POST', self.request)

        eq_(log_cef.call_args[0][0], 'unknown:unknown')
