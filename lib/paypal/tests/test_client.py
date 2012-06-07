import test_utils
import mock
from nose.tools import eq_

from ..client import Client
from ..errors import PaypalError

good_token = {'token': 'foo', 'secret': 'bar'}


@mock.patch.object(Client, '_call')
class TestRefundPermissions(test_utils.TestCase):

    def setUp(self):
        self.paypal = Client()

    def test_get_permissions_url(self, _call):
        _call.return_value = {'token': 'foo'}
        assert 'foo' in self.paypal.get_permission_url('', [])

    def test_get_permissions_url_error(self, _call):
        _call.side_effect = PaypalError
        with self.assertRaises(PaypalError):
            self.paypal.get_permission_url('', [])

    def test_get_permissions_url_scope(self, _call):
        _call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        self.paypal.get_permission_url('', ['REFUND', 'FOO'])
        eq_(_call.call_args[0][1]['scope'], ['REFUND', 'FOO'])

    def test_check_permission_fail(self, _call):
        _call.return_value = {'scope(0)': 'HAM_SANDWICH'}
        assert not self.paypal.check_permission(good_token, ['REFUND'])

    def test_check_permission(self, _call):
        _call.return_value = {'scope(0)': 'REFUND'}
        eq_(self.paypal.check_permission(good_token, ['REFUND']), True)

    def test_check_permission_error(self, _call):
        _call.side_effect = PaypalError
        with self.assertRaises(PaypalError):
            self.paypal.check_permission(good_token, ['REFUND'])

    def test_get_permissions_token(self, _call):
        _call.return_value = {'token': 'foo', 'tokenSecret': 'bar'}
        eq_(self.paypal.get_permission_token('foo', ''), good_token)

    def test_get_permissions_subset(self, _call):
        _call.return_value = {'scope(0)': 'REFUND', 'scope(1)': 'HAM'}
        eq_(self.paypal.check_permission(good_token, ['REFUND', 'HAM']), True)
        eq_(self.paypal.check_permission(good_token, ['REFUND', 'JAM']), False)
        eq_(self.paypal.check_permission(good_token, ['REFUND']), True)
