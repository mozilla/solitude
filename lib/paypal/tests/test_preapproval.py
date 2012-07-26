from datetime import date, timedelta
import json

from django.conf import settings

from mock import patch
from nose.tools import eq_

from lib.buyers.models import Buyer, BuyerPaypal
from solitude.base import APITest


@patch('lib.paypal.client.Client.get_preapproval_key')
@patch.object(settings, 'PAYPAL_USE_SANDBOX', True)
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
        data = json.loads(res.content)
        eq_(data['key'], 'foo')
        eq_(data['paypal_url'],
            'https://www.sandbox.paypal.com/cgi-bin/'
            'webscr?cmd=_ap-preapproval&preapprovalkey=foo')

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

    def test_put_no_buyer(self, key):
        key.return_value = {'key': 'foo'}
        uuid = self.create()
        url = self.get_detail_url('preapproval', uuid)
        eq_(BuyerPaypal.objects.count(), 0)
        res = self.client.put(url)
        eq_(res.status_code, 202)
        eq_(BuyerPaypal.objects.all()[0].key, 'foo')

    def test_put_partial(self, key):
        key.return_value = {'key': 'foo'}
        paypal = BuyerPaypal.objects.create(buyer=self.buyer, currency='BRL')
        eq_(paypal.key, None)
        uuid = self.create()
        url = self.get_detail_url('preapproval', uuid)
        res = self.client.put(url)
        eq_(res.status_code, 202)
        eq_(BuyerPaypal.objects.get(buyer=self.buyer).currency, 'BRL')

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

    def test_delete(self, key):
        key.return_value = {'key': 'foo'}
        BuyerPaypal.objects.create(buyer=self.buyer)
        uuid = self.create()
        url = self.get_detail_url('preapproval', uuid)
        eq_(self.client.delete(url).status_code, 204)
        eq_(self.client.put(url).status_code, 404)
