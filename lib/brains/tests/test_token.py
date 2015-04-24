import json

from solitude.base import APITest

from nose.tools import eq_
from django.core.urlresolvers import reverse


class TestToken(APITest):

    def setUp(self):
        self.url = reverse('braintree:token.generate')

    def test_token(self):
        res = self.client.post(self.url)
        eq_(json.loads(res.content)['token'], 'a-sample-token')
