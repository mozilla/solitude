import json

from nose.tools import eq_

from lib.sellers.tests.utils import make_seller_paypal
from lib.transactions.models import PaypalTransaction
from solitude.base import APITest


class TestSeller(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.list_url = self.get_list_url('transaction')
        self.seller, self.paypal = make_seller_paypal('paypal:%s' % self.uuid)
        self.trans = PaypalTransaction.objects.create(amount=5,
                                                      seller=self.paypal,
                                                      uuid=self.uuid)
        self.detail_url = self.get_detail_url('transaction', self.trans.pk)

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['get'])
        self.allowed_verbs(self.detail_url, ['get'])

    def test_list(self):
        res = self.client.get(self.list_url, data={'uuid': self.uuid})
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['objects'][0]['uuid'], self.uuid)

    def test_get(self):
        res = self.client.get(self.detail_url)
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['uuid'], self.uuid)

    def test_uuid(self):
        res = self.client.get(self.list_url, data={'seller__seller__uuid':
                                                   'paypal:%s' % self.uuid})
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['objects'][0]['uuid'], self.uuid)
