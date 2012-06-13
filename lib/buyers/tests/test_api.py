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
        self.allowed_verbs(self.list_url, ['post'])

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


@patch('lib.buyers.resource.Client.get_preapproval_key')
class TestPreapprovalPaypal(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.list_url = self.get_list_url('preapproval')
        self.buyer = Buyer.objects.create(uuid=self.uuid)

    def get_data(self):
        return {'start': date.today().strftime('%Y-%m-%d'),
                'end': (date.today() +
                        timedelta(days=30)).strftime('%Y-%m-%d'),
                'return_url': 'http://foo.com/return.url',
                'cancel_url': 'http://foo.com/cancel.url',
                'uuid': self.uuid}

    def test_post(self, key):
        key.return_value = {'key': 'foo'}
        res = self.client.post(self.list_url, data=self.get_data())
        eq_(res.status_code, 201, res.content)
        # Note: the key needs to be disclosed here so it can be passed
        # on to client to ask PayPal. This is the only time it should
        # be disclosed however.
        eq_(json.loads(res.content)['key'], 'foo')

    def test_post_empty(self, key):
        res = self.client.post(self.list_url, data={})
        eq_(res.status_code, 400)
        data = json.loads(res.content)
        for k in ['start', 'end', 'return_url', 'cancel_url']:
            eq_(data[k], [u'This field is required.'])

    def test_post_not_date(self, key):
        data = self.get_data()
        data['start'] = '2012'
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)
        eq_(json.loads(res.content)['start'], [u'Enter a valid date.'])

    def test_post_not_url(self, key):
        data = self.get_data()
        data['return_url'] = 'blargh'
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)
        eq_(json.loads(res.content)['return_url'], [u'Enter a valid URL.'])

    def create(self):
        res = self.client.post(self.list_url, data=self.get_data())
        return json.loads(res.content)['pk']

    def test_get(self, key):
        key.return_value = {'key': 'foo'}
        uuid = self.create()
        url = self.get_detail_url('preapproval', uuid)
        res = self.client.get(url)
        assert 'foo' not in res  # Just check we didn't leak the key.

    def test_put(self, key):
        key.return_value = {'key': 'foo'}
        paypal = BuyerPaypal.objects.create(buyer=self.buyer)
        eq_(paypal.key, None)
        uuid = self.create()
        url = self.get_detail_url('preapproval', uuid)
        res = self.client.put(url)
        eq_(res.status_code, 202)
        eq_(BuyerPaypal.objects.get(buyer=self.buyer).key, 'foo')

    def test_put_fails(self, key):
        url = self.get_detail_url('preapproval', 'asd')
        res = self.client.put(url)
        eq_(res.status_code, 404, res.content)

    def test_put_no_cache(self, key):
        key.return_value = {'key': 'foo'}
        paypal = BuyerPaypal.objects.create(buyer=self.buyer)
        eq_(paypal.key, None)

        url = self.get_detail_url('preapproval', '123')
        res = self.client.put(url)
        eq_(res.status_code, 404)
