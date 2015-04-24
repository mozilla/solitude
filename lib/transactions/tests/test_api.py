from django.core.urlresolvers import reverse

from nose.tools import eq_, ok_

from lib.bango.tests.utils import make_sellers
from lib.buyers.models import Buyer
from lib.transactions import constants
from lib.transactions.models import Transaction
from solitude.base import APITest


class TestTransaction(APITest):

    def setUp(self):
        self.api_name = 'generic'
        self.uuid = 'sample:uid'
        self.list_url = reverse('generic:transaction-list')
        self.buyer = Buyer.objects.create(uuid='buyer_uuid')
        self.sellers = make_sellers('sample:uid')
        self.product = self.sellers.product
        self.trans = Transaction.objects.create(
            amount=5, seller_product=self.sellers.product,
            provider=constants.PROVIDER_BANGO, uuid=self.uuid)
        self.detail_url = self.trans.get_uri()

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['get', 'post'])
        self.allowed_verbs(self.detail_url, ['get', 'patch'])

    def test_list(self):
        res = self.client.get(self.list_url, {'uuid': self.uuid})
        eq_(res.status_code, 200)
        eq_(res.json['objects'][0]['uuid'], self.uuid)

    def test_get(self):
        res = self.client.get(self.detail_url)
        eq_(res.status_code, 200)
        eq_(res.json['uuid'], self.uuid)

    def test_status_reason(self):
        data = {'status_reason': 'OOPS'}
        eq_(self.client.patch(self.detail_url, data=data).status_code, 200)
        res = self.client.get(self.detail_url)
        eq_(res.json['status_reason'], 'OOPS')

    def test_post_uuid(self):
        data = {
            'provider': constants.PROVIDER_BANGO,
            'seller_product': '/generic/product/{product_id}/'.format(
                product_id=self.product.pk),
            'seller': '/generic/seller/{seller_id}/'.format(
                seller_id=self.sellers.seller.pk),
            'buyer': '/generic/buyer/{buyer_id}/'.format(
                buyer_id=self.buyer.pk),
            'status_reason': 'ALL_COOL',
        }
        res = self.client.post(self.list_url, data=data)

        eq_(res.status_code, 201)

        json_data = res.json
        transaction = Transaction.objects.get(uuid=json_data['uuid'])

        eq_(transaction.buyer, self.buyer)
        eq_(transaction.provider, constants.PROVIDER_BANGO)
        eq_(transaction.seller, self.sellers.seller)
        eq_(transaction.seller_product, self.product)

    def test_provider(self):
        res = self.client.get(self.list_url,
                              {'provider': constants.PROVIDER_BOKU})
        eq_(res.status_code, 200)
        eq_(res.json['meta']['total_count'], 0, res.content)

    def test_provider_patch(self):
        self.trans.provider = None
        self.trans.save()
        res = self.client.patch(
            self.detail_url, data={'provider': constants.PROVIDER_BOKU})
        eq_(res.status_code, 200, res.content)
        res = self.client.patch(
            self.detail_url, data={'provider': constants.PROVIDER_BANGO})
        eq_(res.status_code, 400, res.content)

    def test_patch(self):
        res = self.client.patch(
            self.detail_url, data={'status': constants.STATUS_COMPLETED})
        eq_(res.status_code, 200, res.content)
        eq_(Transaction.objects.get(pk=self.trans.pk).status,
            constants.STATUS_COMPLETED)

    def test_patch_naughty(self):
        res = self.client.patch(self.detail_url, data={'uuid': 5})
        eq_(res.status_code, 400)
        eq_(res.json['__all__'], ['Cannot alter fields: uuid'])

    def test_patch_uid_pay(self):
        res = self.client.patch(self.detail_url, data={'uid_pay': 'xyz'})
        eq_(res.status_code, 200)
        eq_(self.trans.reget().uid_pay, 'xyz')

    def test_patch_pay_url(self):
        pay_url = 'https://bango.com/pay'
        res = self.client.patch(self.detail_url, data={'pay_url': pay_url})
        eq_(res.status_code, 200, res.content)
        eq_(self.trans.reget().pay_url, pay_url)

    def test_invalid_pay_url(self):
        res = self.client.patch(self.detail_url, data={'pay_url': 'not-a-url'})
        eq_(res.status_code, 400, res.content)

    def test_patch_status(self):
        self.trans.status = constants.STATUS_FAILED
        self.trans.save()
        res = self.client.patch(self.detail_url,
                                data={'status': constants.STATUS_COMPLETED})
        eq_(res.status_code, 400, res.content)

    def test_patch_status_errored(self):
        self.trans.status = constants.STATUS_ERRORED
        self.trans.save()
        res = self.client.patch(self.detail_url,
                                data={'status': constants.STATUS_COMPLETED})
        eq_(res.status_code, 400, res.content)

    def test_relations(self):
        new_uuid = self.uuid + ':refund'
        new = Transaction.objects.create(amount=5, seller_product=self.product,
                                         provider=constants.PROVIDER_BANGO,
                                         related=self.trans, uuid=new_uuid,
                                         uid_pay='1')

        # The original transaction has nothing related to it and some
        # relations that are fully populated.
        res = self.client.get(self.list_url, {'uuid': self.uuid})
        eq_(res.json['objects'][0]['related'], None)
        eq_(res.json['objects'][0]['relations'][0]['resource_pk'], new.pk)

        # The related transaction has no relations, but a pointer to the
        # related transaction.
        res = self.client.get(self.list_url, {'uuid': new_uuid})
        eq_(res.json['objects'][0]['relations'], [])
        eq_(res.json['objects'][0]['related'],
            '/generic/transaction/%s/' % self.trans.pk)

    def test_create_minimal(self):
        res = self.client.post(self.list_url, data={})
        eq_(res.status_code, 201)
        eq_(res.json['status'], constants.STATUS_STARTED)

    def test_patch_minimal(self):
        res = self.client.post(self.list_url, data={})
        res = self.client.patch(res.json['resource_uri'],
                                data={'status': constants.STATUS_ERRORED})
        eq_(res.status_code, 200, res.content)

    def test_patch_minimal_fails(self):
        res = self.client.post(self.list_url, data={})
        res = self.client.patch(res.json['resource_uri'],
                                data={'status': constants.STATUS_COMPLETED})
        eq_(res.status_code, 400, res.content)

    def test_post_no_uuid(self):
        res = self.client.post(self.list_url)
        ok_(res.json['uuid'].startswith('solitude:'))

    def test_patch_no_uuid(self):
        res = self.client.post(self.list_url, data={'uuid': 'test:uuid'})
        res = self.client.patch(res.json['resource_uri'],
                                data={'status': constants.STATUS_ERRORED})
        eq_(res.json['uuid'], 'test:uuid')
