import json

from nose.tools import eq_

from lib.buyers.models import Buyer
from solitude.base import APITest


class TestBuyer(APITest):

    def setUp(self):
        self.list_url = self.get_list_url('buyer')
        self.uuid = 'sample:uid'

    def test_add(self):
        res = self.client.post(self.list_url, data={'uuid': self.uuid})
        eq_(res.status_code, 201)
        eq_(Buyer.objects.filter(uuid=self.uuid).count(), 1)

    def test_add_multiple(self):
        self.client.post(self.list_url, data={'uuid':self.uuid})
        res = self.client.post(self.list_url, data={'uuid':self.uuid})
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'uuid'),
            # How do we stop uuid being capitalized?
            ['Buyer with this Uuid already exists.'])

    def test_add_empty(self):
        res = self.client.post(self.list_url, data={'uuid':''})
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

    def test_list_allowed(self):
        obj = self.create()
        self.allowed_verbs(self.get_detail_url('buyer', obj), ['get'])
