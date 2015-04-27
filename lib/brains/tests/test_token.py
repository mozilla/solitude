from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.brains.tests.base import BraintreeTest


class TestToken(BraintreeTest):

    def test_token(self):
        self.set_mocks(['POST', 'client_token', 200, 'token'])
        res = self.client.post(reverse('braintree:token.generate'))
        eq_(res.json['token'], 'a-sample-token')
