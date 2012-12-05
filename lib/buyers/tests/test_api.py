import json

from nose.tools import eq_

from lib.buyers.models import Buyer, BuyerPaypal
from solitude.base import APITest


class TestBuyer(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.uuid = 'sample:uid'
        self.pin = '1234'
        self.list_url = self.get_list_url('buyer')

    def test_add(self):
        res = self.client.post(self.list_url, data={'uuid': self.uuid,
                                                    'pin': self.pin})
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
        self.allowed_verbs(self.list_url, ['post', 'get', 'put'])

    def test_filter(self):
        self.client.post(self.list_url, data={'uuid': self.uuid})
        res = self.client.get(self.list_url + '?uuid=%s' % self.uuid)
        eq_(res.status_code, 200)
        data = json.loads(res.content)
        eq_(data['meta']['total_count'], 1)
        eq_(data['objects'][0]['uuid'], self.uuid)

    def create(self, **kwargs):
        defaults = {'uuid': self.uuid, 'pin': self.pin}
        defaults.update(kwargs)
        return Buyer.objects.create(**defaults)

    def test_get(self):
        obj = self.create()
        res = self.client.get(self.get_detail_url('buyer', obj))
        eq_(res.status_code, 200)
        eq_(json.loads(res.content)['uuid'], self.uuid)

    def test_detail_allowed_verbs(self):
        obj = self.create()
        self.allowed_verbs(self.get_detail_url('buyer', obj), ['get', 'patch',
                                                               'put'])

    def test_put_pin(self):
        obj = self.create()
        new_pin = self.pin[::-1]  # reverse it so it is different
        assert(obj.pin.check(self.pin))
        detail_url = self.get_detail_url('buyer', obj)
        res = self.client.put(detail_url, data={'uuid': obj.uuid,
                                                'pin': new_pin})
        eq_(res.status_code, 202)
        obj = Buyer.objects.get(pk=obj.pk)
        assert(obj.pin.check(new_pin))

    def test_patch_pin(self):
        obj = self.create()
        old = obj.pin
        res = self.client.patch(self.get_detail_url('buyer', obj),
                                data={'pin': '1234'})
        eq_(res.status_code, 202)
        assert obj.reget().pin != old

    def test_patch_uuid(self):
        obj = self.create()
        res = self.client.patch(self.get_detail_url('buyer', obj),
                                data={'uuid': self.uuid + ':new',
                                      'pin': '1234'})
        eq_(res.status_code, 202)
        eq_(obj.reget().uuid, self.uuid + ':new')

    def test_patch_same_uuid(self):
        obj = self.create()
        res = self.client.patch(self.get_detail_url('buyer', obj),
                                data={'uuid': self.uuid,
                                      'pin': '1234'})
        eq_(res.status_code, 202)
        eq_(obj.reget().uuid, self.uuid)


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

    def test_list_allowed(self):
        obj = self.create()
        url = self.get_detail_url('buyer', obj)

        self.allowed_verbs(self.list_url, ['post'])
        self.allowed_verbs(url, ['get', 'delete', 'patch'])

    def test_delete(self):
        obj = self.create()
        url = self.get_detail_url('buyer', obj)
        res = self.client.delete(url, data={'uuid': self.uuid})
        eq_(res.status_code, 204)
        eq_(BuyerPaypal.objects.count(), 0)

    def test_patch(self):
        obj = self.create()
        obj.key = 'foofy'
        obj.save()
        url = self.get_detail_url('buyer', obj)
        res = self.client.patch(url, data={'currency': 'BRL'})
        eq_(res.status_code, 202)
        res = BuyerPaypal.objects.all()
        eq_(res.count(), 1)
        eq_(res[0].currency, 'BRL')
        eq_(res[0].key, 'foofy')  # Ensure key hasn't changed.

    def test_patch_key(self):
        obj = self.create()
        url = self.get_detail_url('buyer', obj)
        obj.key = 'foobar'
        obj.save()
        self.client.patch(url, data={'key': ''})
        eq_(BuyerPaypal.objects.get(pk=obj.pk).key, None)


class TestBuyerVerifyPin(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.uuid = 'sample:uid'
        self.pin = '1234'
        self.buyer = Buyer.objects.create(uuid=self.uuid, pin=self.pin)
        self.list_url = self.get_list_url('verify_pin')

    def test_good_uuid_and_pin(self):
        res = self.client.post(self.list_url, data={'uuid': self.uuid,
                                                    'pin': self.pin})
        eq_(res.status_code, 201)
        data = json.loads(res.content)
        assert data['valid']
        eq_(data['uuid'], self.uuid)

    def test_good_uuid_and_bad_pin(self):
        res = self.client.post(self.list_url, data={'uuid': self.uuid,
                                                    'pin': '4321'})
        eq_(res.status_code, 201)
        data = json.loads(res.content)
        assert not data['valid']
        eq_(data['uuid'], self.uuid)

    def test_bad_uuid(self):
        res = self.client.post(self.list_url, data={'uuid': 'bad:uuid',
                                                    'pin': '4321'})
        eq_(res.status_code, 404)

    def test_empty_post(self):
        res = self.client.post(self.list_url, data={})
        eq_(res.status_code, 400)
