import json

from nose.tools import eq_

from lib.sellers.models import Seller, SellerPaypal
from solitude.base import APITest


class TestSeller(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.uuid = 'sample:uid'
        self.list_url = self.get_list_url('seller')

    def test_add(self):
        res = self.client.post(self.list_url, data={'uuid': self.uuid})
        eq_(res.status_code, 201)
        eq_(Seller.objects.filter(uuid=self.uuid).count(), 1)

    def test_add_multiple(self):
        self.client.post(self.list_url, data={'uuid': self.uuid})
        res = self.client.post(self.list_url, data={'uuid': self.uuid})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'),
            ['Seller with this Uuid already exists.'])

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
        return Seller.objects.create(uuid=self.uuid)

    def test_get(self):
        obj = self.create()
        res = self.client.get(self.get_detail_url('seller', obj))
        eq_(res.status_code, 200)
        content = json.loads(res.content)
        eq_(content['uuid'], self.uuid)
        eq_(content['resource_pk'], obj.pk)


class TestSellerPaypal(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.seller = Seller.objects.create(uuid=self.uuid)
        self.list_url = self.get_list_url('seller')

    def test_post(self):
        res = self.client.post(self.list_url,
                               data={'seller':
                                     '/paypal/seller/%s/' % self.seller.pk,
                                     'paypal_id': 'foo@bar.com'})
        eq_(res.status_code, 201)
        objs = SellerPaypal.objects.all()
        eq_(objs.count(), 1)
        eq_(objs[0].paypal_id, 'foo@bar.com')

    def test_get(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)
        res = self.client.get(url)
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['token'], False)
        eq_(json.loads(res.content)['secret'], False)

    def test_get_generic(self):
        self.create()
        url = self.get_detail_url('seller', self.seller, api_name='generic')
        res = self.client.get(url)
        eq_(res.status_code, 200)
        content = json.loads(res.content)
        eq_(content['paypal']['token'], False)
        eq_(content['paypal']['secret'], False)

    def create(self):
        return SellerPaypal.objects.create(seller=self.seller)

    def test_booleans(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)

        res = self.client.get(url, data={'uuid': self.uuid})
        content = json.loads(res.content)
        eq_(content['secret'], False)
        eq_(content['token'], False)

        obj.token = obj.secret = 'abc'
        obj.save()

        res = self.client.get(url, data={'uuid': self.uuid})
        content = json.loads(res.content)
        eq_(content['secret'], True)
        eq_(content['token'], True)

    def test_set_paypal_id(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)
        id_ = 'foo@bar.com'
        res = self.client.put(url, data={'paypal_id': id_})
        eq_(res.status_code, 202)
        eq_(json.loads(res.content)['paypal_id'], id_)
