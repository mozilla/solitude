import urllib

import test_utils
import mock
from nose.tools import eq_

from ..client import Client
from ..errors import PaypalError

good_token = urllib.urlencode({'token': 'foo', 'secret': 'bar'})


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
