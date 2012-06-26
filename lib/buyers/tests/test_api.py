from datetime import date, timedelta
import json

from mock import patch
from nose.tools import eq_

from lib.buyers.models import Buyer, BuyerPaypal
from solitude.base import APITest


class TestBuyer(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.uuid = 'sample:uid'
        self.list_url = self.get_list_url('buyer')

    def test_add(self):
        res = self.client.post(self.list_url, data={'uuid': self.uuid})
        eq_(res.status_code, 201)
        eq_(Buyer.objects.filter(uuid=self.uuid).count(), 1)

    def test_add_multiple(self):
        self.client.post(self.list_url, data={'uuid': self.uuid})
        res = self.client.post(self.list_url, data={'uuid': self.uuid})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'),
            # How do we stop uuid being capitalized?
            ['Buyer with this Uuid already exists.'])

    def test_add_empty(self):
        res = self.client.post(self.list_url, data={'uuid': ''})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'), ['This field is required.'])

    def test_add_missing(self):
        res = self.client.post(self.list_url, data={})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'), ['This field is required.'])

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post', 'get'])

    def test_filter(self):
        self.client.post(self.list_url, data={'uuid': self.uuid})
        res = self.client.get(self.list_url + '?uuid=%s' % self.uuid)
        eq_(res.status_code, 200)
        data = json.loads(res.content)
        eq_(data['meta']['total_count'], 1)
        eq_(data['objects'][0]['uuid'], self.uuid)

    def create(self):
        return Buyer.objects.create(uuid=self.uuid)

    def test_get(self):
        obj = self.create()
        res = self.client.get(self.get_detail_url('buyer', obj))
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['uuid'], self.uuid)

    def test_get_allowed(self):
        obj = self.create()
        self.allowed_verbs(self.get_detail_url('buyer', obj), ['get'])


class TestBuyerPaypal(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.buyer = Buyer.objects.create(uuid=self.uuid)
        self.list_url = self.get_list_url('buyer')

    def test_post(self):
        res = self.client.post(self.list_url,
                               data={'buyer':
                                     '/paypal/buyer/%s/' % self.buyer.pk})
        eq_(res.status_code, 201)
        eq_(BuyerPaypal.objects.count(), 1)

    def test_get(self):
        obj = self.create()
        url = self.get_detail_url('buyer', obj)
        res = self.client.get(url)
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['key'], False)

    def test_get_generic(self):
        self.create()
        url = self.get_detail_url('buyer', self.buyer, api_name='generic')
        res = self.client.get(url)
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['paypal']['key'], False)

    def create(self):
        return BuyerPaypal.objects.create(buyer=self.buyer)

    def test_boolean_key(self):
        obj = self.create()
        url = self.get_detail_url('buyer', obj)

        res = self.client.get(url, data={'uuid': self.uuid})
        eq_(json.loads(res.content)['key'], False)

        obj.key = 'abc'
        obj.save()

        res = self.client.get(url, data={'uuid': self.uuid})
        eq_(json.loads(res.content)['key'], True)
