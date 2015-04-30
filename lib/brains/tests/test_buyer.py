import uuid

from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.brains.models import BraintreeBuyer
from lib.brains.tests.base import BraintreeTest
from lib.buyers.models import Buyer


class TestCustomer(BraintreeTest):

    def setUp(self):
        self.url = reverse('braintree:buyer-list')

    def test_allowed(self):
        self.allowed_verbs(self.url, ['get'])

    def create_buyer(self):
        buyer = Buyer.objects.create(uuid=str(uuid.uuid4()))
        braintree_buyer = BraintreeBuyer.objects.create(
            braintree_id='sample:id', buyer=buyer)
        return buyer, braintree_buyer

    def test_patch_ok(self):
        buyer, braintree_buyer = self.create_buyer()
        url = reverse('braintree:buyer-detail',
                      kwargs={'pk': braintree_buyer.pk})
        self.client.patch(url, {'active': False})
        res = self.client.get(url)
        eq_(res.json['braintree_id'], '{0}'.format(buyer.pk))

    def test_patch_readonly(self):
        buyer, braintree_buyer = self.create_buyer()
        url = reverse('braintree:buyer-detail',
                      kwargs={'pk': braintree_buyer.pk})
        self.client.patch(url, {'active': False, 'braintree_id': 'foo'})
        res = self.client.get(url)
        eq_(res.json['braintree_id'], '{0}'.format(buyer.pk))

    def test_lookup(self):
        self.create_buyer()
        buyer, braintree_buyer = self.create_buyer()
        res = self.client.get(self.url, {'buyer': buyer.pk})
        eq_(res.json['meta']['total_count'], 1)
        eq_(res.json['objects'][0]['id'], braintree_buyer.pk)
