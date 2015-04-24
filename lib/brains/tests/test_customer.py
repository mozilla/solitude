from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.brains.forms import BuyerForm
from lib.brains.tests.base import BraintreeTest
from lib.buyers.models import Buyer


class TestCustomer(BraintreeTest):

    def setUp(self):
        super(TestCustomer, self).setUp()
        self.url = reverse('braintree:customer')

    def test_solitude_buyer_exists(self):
        self.set_mocks(
            ('GET', 'customers/minimal', 404, 'customer-minimal'),
            ('POST', 'customers', 201, 'customer-minimal')
        )
        buyer = Buyer.objects.create(uuid='minimal')
        res = self.client.post(self.url, data={'uuid': 'minimal'})
        eq_(res.status_code, 201)
        eq_(Buyer.objects.count(), 1)
        eq_(res.json['resource_pk'], buyer.pk)

    def test_solitude_buyer_doesnt_exist(self):
        self.set_mocks(
            ('GET', 'customers/minimal', 200, 'customer-minimal')
        )
        res = self.client.post(self.url, data={'uuid': 'minimal'})
        eq_(res.status_code, 201)
        buyer = Buyer.objects.get()
        eq_(buyer.uuid, 'minimal')

    def test_braintree_buyer_does_exist(self):
        self.set_mocks(
            ('GET', 'customers/minimal', 200, 'customer-minimal'),
        )
        res = self.client.post(self.url, data={'uuid': 'minimal'})
        eq_(res.status_code, 201)
        eq_(res.json['braintree']['id'], 'minimal')

    def test_both_exist(self):
        self.set_mocks(
            ('GET', 'customers/minimal', 200, 'customer-minimal'),
        )
        Buyer.objects.create(uuid='minimal')
        res = self.client.post(self.url, data={'uuid': 'minimal'})
        eq_(res.status_code, 200)

    def test_braintree_buyer_doesnt_exist(self):
        self.set_mocks(
            ('GET', 'customers/minimal', 404, 'customer-minimal'),
            ('POST', 'customers', 201, 'customer-minimal')
        )
        res = self.client.post(self.url, data={'uuid': 'minimal'})
        eq_(res.status_code, 201)
        eq_(res.json['braintree']['id'], 'minimal')

    def test_braintree_other_error(self):
        self.set_mocks(
            ('GET', 'customers/minimal', 404, 'customer-minimal'),
            ('POST', 'customers', 422, 'customer-error')
        )
        res = self.client.post(self.url, data={'uuid': 'minimal'})
        eq_(Buyer.objects.count(), 0)
        eq_(res.status_code, 400)
        eq_(res.json['__type__'], 'braintree')

    def test_no_uuid(self):
        res = self.client.post(self.url, data={})
        eq_(res.status_code, 400)
        eq_(res.json['uuid'][0],
            unicode(BuyerForm().fields['uuid'].error_messages['required']))
