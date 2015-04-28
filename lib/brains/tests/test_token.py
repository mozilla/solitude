from django.core.urlresolvers import reverse

from braintree.client_token_gateway import ClientTokenGateway
from nose.tools import eq_

from lib.brains.tests.base import BraintreeTest


class TestToken(BraintreeTest):
    gateways = {'client': ClientTokenGateway}

    def test_token(self):
        self.mocks['client'].generate.return_value = 'a-sample-token'
        res = self.client.post(reverse('braintree:token.generate'))
        eq_(res.json['token'], 'a-sample-token')
