from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.brains.tests.base import BraintreeTest, create_buyer


class TestCustomer(BraintreeTest):

    def setUp(self):
        self.url = reverse('braintree:mozilla:buyer-list')

    def test_allowed(self):
        self.allowed_verbs(self.url, ['get'])

    def test_patch_ok(self):
        buyer, braintree_buyer = create_buyer()
        url = reverse('braintree:mozilla:buyer-detail',
                      kwargs={'pk': braintree_buyer.pk})
        self.client.patch(url, {'active': False})
        res = self.client.get(url)
        eq_(res.json['braintree_id'], '{0}'.format(buyer.pk))

    def test_patch_readonly(self):
        buyer, braintree_buyer = create_buyer()
        url = reverse('braintree:mozilla:buyer-detail',
                      kwargs={'pk': braintree_buyer.pk})
        self.client.patch(url, {'active': False, 'braintree_id': 'foo'})
        res = self.client.get(url)
        eq_(res.json['braintree_id'], '{0}'.format(buyer.pk))

    def test_lookup(self):
        create_buyer()
        buyer, braintree_buyer = create_buyer()
        res = self.client.get(self.url, {'buyer': buyer.pk})
        eq_(res.json['meta']['total_count'], 1)
        eq_(res.json['objects'][0]['id'], braintree_buyer.pk)
