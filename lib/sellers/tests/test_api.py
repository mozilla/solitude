import json

from nose.tools import eq_

from lib.sellers.constants import EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE
from lib.sellers.models import Seller, SellerProduct, SellerPaypal
from solitude.base import APITest

uuid = 'sample:uid'


class TestSeller(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.list_url = self.get_list_url('seller')

    def test_add(self):
        res = self.client.post(self.list_url, data={'uuid': uuid})
        eq_(res.status_code, 201)
        eq_(Seller.objects.filter(uuid=uuid).count(), 1)

    def test_add_multiple(self):
        self.client.post(self.list_url, data={'uuid': uuid})
        res = self.client.post(self.list_url, data={'uuid': uuid})
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
        self.allowed_verbs(self.list_url, ['post', 'get'])

    def create(self):
        return Seller.objects.create(uuid=uuid)

    def test_get(self):
        obj = self.create()
        res = self.client.get(self.get_detail_url('seller', obj))
        eq_(res.status_code, 200)
        content = json.loads(res.content)
        eq_(content['uuid'], uuid)
        eq_(content['resource_pk'], obj.pk)


class TestSellerPaypal(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.seller = Seller.objects.create(uuid=uuid)
        self.list_url = self.get_list_url('seller')

    def data(self):
        return {'seller': '/generic/seller/%s/' % self.seller.pk,
                'paypal_id': 'foo@bar.com',
                'address_one': '123 main st.',
                'country': 'canada'}

    def test_post(self):
        res = self.client.post(self.list_url, data=self.data())
        eq_(res.status_code, 201)
        objs = SellerPaypal.objects.all()
        eq_(objs.count(), 1)
        eq_(objs[0].paypal_id, 'foo@bar.com')
        eq_(objs[0].address_one, '123 main st.')

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
        return SellerPaypal.objects.create(seller=self.seller,
                                           address_one='123 main st.')

    def test_booleans(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)

        res = self.client.get(url, data={'uuid': uuid})
        content = json.loads(res.content)
        eq_(content['secret'], False)
        eq_(content['token'], False)

        obj.token = obj.secret = 'abc'
        obj.save()

        res = self.client.get(url, data={'uuid': uuid})
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

    def test_patch(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)
        id_ = 'foo@bar.com'
        secret = 'some-secret'
        obj.secret = secret
        obj.save()

        res = self.client.patch(url, data={'paypal_id': id_})
        eq_(res.status_code, 202, res.content)
        res = SellerPaypal.objects.get(pk=obj.pk)
        eq_(res.secret, secret)
        eq_(res.paypal_id, id_)
        eq_(res.address_one, '123 main st.')

    def test_list_allowed(self):
        obj = self.create()
        url = self.get_detail_url('seller', obj)

        self.allowed_verbs(self.list_url, ['post', 'get'])
        self.allowed_verbs(url, ['get', 'delete', 'put', 'patch'])


class TestSellerProduct(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.seller = Seller.objects.create(uuid=uuid)
        self.seller_url = self.get_detail_url('seller', self.seller.pk)
        self.list_url = self.get_list_url('product')

    def create(self, **kw):
        params = {'seller': self.seller, 'external_id': 'xyz',
                  'public_id': uuid}
        params.update(kw)
        return SellerProduct.objects.create(**params)

    def create_url(self):
        obj = self.create(public_id='%s-url' % uuid)
        url = self.get_detail_url('product', obj)
        return obj, url

    def data(self, **kw):
        params = {'seller': self.seller_uri(),
                  'external_id': 'pre-generated-product-id',
                  'secret': 'hush',
                  'public_id': 'public-id'}
        params.update(**kw)
        return params

    def seller_uri(self):
        return self.get_detail_url('seller', self.seller.pk)

    def test_get_miss(self):
        # A test that filtering on the wrong uuid returns zero.
        self.create()
        res = self.client.get(self.list_url, data={'seller__uuid': 'foo'})
        eq_(json.loads(res.content)['meta']['total_count'], 0)

    def test_get_all(self):
        # No filters at all still returns everything.
        self.create()
        res = self.client.get(self.list_url)
        eq_(json.loads(res.content)['meta']['total_count'], 1)

    def test_get_one(self):
        # Getting just one object just works.
        self.create()
        res = self.client.get(self.list_url, data={'seller__uuid': uuid})
        eq_(json.loads(res.content)['meta']['total_count'], 1)

    def test_not_active(self):
        obj = self.create()
        obj.seller.active = False
        obj.seller.save()
        res = self.client.get(self.list_url, data={'seller__uuid': uuid,
                                                   'seller__active': True})
        eq_(json.loads(res.content)['meta']['total_count'], 0)

    def test_post(self):
        res = self.client.post(self.list_url, data=self.data())
        eq_(res.status_code, 201)
        objs = SellerProduct.objects.all()
        eq_(objs.count(), 1)

    def test_get_by_external_id(self):
        prod = self.create(external_id='my-id')
        res = self.client.get(self.list_url, data={'seller': self.seller.pk,
                                                   'external_id': 'my-id'})
        eq_(res.status_code, 200)
        data = json.loads(res.content)
        eq_(data['meta']['total_count'], 1)
        eq_(data['objects'][0]['resource_pk'], prod.pk)

    def test_get_by_public_id(self):
        self.create(public_id='one', external_id='one')
        self.create(public_id='two', external_id='two')
        res = self.client.get(self.list_url, data={'seller': self.seller.pk,
                                                   'public_id': 'one'})
        eq_(res.status_code, 200, res)
        data = json.loads(res.content)
        eq_(data['meta']['total_count'], 1)
        eq_(data['objects'][0]['public_id'], 'one')

    def test_id_unique_for_seller_error(self):
        res = self.client.post(self.list_url,
                               data=self.data(external_id='unique-id'))
        eq_(res.status_code, 201, res.content)
        # Submit the same ID for the same seller.
        res = self.client.post(self.list_url,
                               data=self.data(external_id='unique-id'))
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, '__all__'),
            [EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE], res.content)

    def test_id_unique_for_seller_ok(self):
        res = self.client.post(self.list_url,
                               data=self.data(external_id='unique-id'))
        eq_(res.status_code, 201)

        new_seller = Seller.objects.create(uuid='some-other-seller')

        data = self.data(seller=self.get_detail_url('seller', new_seller.pk),
                         external_id='unique-id', public_id='blah')
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 201)

    def test_list_allowed(self):
        obj, url = self.create_url()

        self.allowed_verbs(self.list_url, ['post', 'get'])
        self.allowed_verbs(url, ['get', 'put', 'patch'])

    def test_patch_get_secret(self):
        obj, url = self.create_url()
        res = self.client.patch(url, json.dumps({'seller': self.seller_url,
                                                 'external_id': 'xyz',
                                                 'secret': 'hush'}))
        eq_(res.status_code, 202, res.content)
        res = self.client.get(url)
        data = json.loads(res.content)
        eq_(data['secret'], 'hush')

    def test_patch_get_ext_id(self):
        obj, url = self.create_url()
        res = self.client.patch(url, json.dumps({'seller': self.seller_url,
                                                 'external_id': 'some-id'}))
        eq_(res.status_code, 202)
        data = obj.reget()
        eq_(data.external_id, 'some-id')

    def test_put_get(self):
        obj, url = self.create_url()
        res = self.client.put(url, json.dumps({'seller': self.seller_url,
                                               'secret': 'hush',
                                               'external_id': 'abc',
                                               'public_id': 'blah'}))
        eq_(res.status_code, 202)
        data = obj.reget()
        eq_(data.secret, 'hush')
        eq_(data.external_id, 'abc')

    def test_patch_non_unique_ext_id(self):
        self.create(external_id='some-id')
        obj, url = self.create_url()
        res = self.client.patch(url, json.dumps({'external_id': 'some-id'}))
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, '__all__'),
            [EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE], res.content)

    def test_put_non_unique_ext_id(self):
        self.create(external_id='some-id')
        obj, url = self.create_url()
        res = self.client.put(url, json.dumps({'seller': self.seller_url,
                                               'secret': 'hush',
                                               'external_id': 'some-id',
                                               'public_id': 'blah'}))
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, '__all__'),
            [EXTERNAL_PRODUCT_ID_IS_NOT_UNIQUE], res.content)
