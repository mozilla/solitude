from datetime import datetime

from django.core.urlresolvers import reverse

from braintree.customer import Customer
from braintree.customer_gateway import CustomerGateway
from braintree.error_result import ErrorResult
from braintree.exceptions import NotFoundError
from braintree.successful_result import SuccessfulResult
from nose.tools import eq_

from lib.brains.forms import BuyerForm
from lib.brains.models import BraintreeBuyer
from lib.brains.tests.base import BraintreeTest
from lib.buyers.models import Buyer


def customer(**kw):
    customer = {
        'id': 'customer-id',
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    customer.update(**kw)
    return Customer(None, customer)


def successful_customer(**kw):
    return SuccessfulResult({'customer': customer(**kw)})


def error():
    return ErrorResult(None, {'errors': {}, 'message': ''})


class TestCustomer(BraintreeTest):
    gateways = {'customer': CustomerGateway}

    def setUp(self):
        super(TestCustomer, self).setUp()
        self.url = reverse('braintree:customer')

    def test_solitude_buyer_exists(self):
        self.mocks['customer'].find.side_effect = NotFoundError
        self.mocks['customer'].create.return_value = successful_customer()

        buyer = Buyer.objects.create(uuid='customer-id')
        BraintreeBuyer.objects.create(buyer=buyer)
        res = self.client.post(self.url, data={'uuid': 'customer-id'})
        eq_(res.status_code, 201)
        eq_(Buyer.objects.count(), 1)
        eq_(BraintreeBuyer.objects.count(), 1)
        eq_(res.json['resource_pk'], buyer.pk)

    def test_solitude_buyer_doesnt_exist(self):
        self.mocks['customer'].find.return_value = customer()

        res = self.client.post(self.url, data={'uuid': 'customer-id'})
        eq_(res.status_code, 201)
        buyer = Buyer.objects.get()
        eq_(buyer.uuid, 'customer-id')
        braintree_buyer = BraintreeBuyer.objects.get()
        eq_(braintree_buyer.braintree_id, str(buyer.pk))

    def test_braintree_buyer_does_exist(self):
        self.mocks['customer'].find.return_value = customer()

        res = self.client.post(self.url, data={'uuid': 'customer-id'})
        eq_(res.status_code, 201)
        eq_(res.json['braintree']['id'], 'customer-id')

    def test_both_exist(self):
        self.mocks['customer'].find.return_value = customer()

        Buyer.objects.create(uuid='minimal')
        res = self.client.post(self.url, data={'uuid': 'customer-id'})
        eq_(res.status_code, 201)

    def test_braintree_buyer_doesnt_exist(self):
        self.mocks['customer'].find.side_effect = NotFoundError
        self.mocks['customer'].create.return_value = successful_customer()

        res = self.client.post(self.url, data={'uuid': 'customer-id'})
        eq_(res.status_code, 201)
        eq_(res.json['braintree']['id'], 'customer-id')

    def test_no_uuid(self):
        res = self.client.post(self.url, data={})
        eq_(res.status_code, 400)
        eq_(res.json['uuid'][0],
            unicode(BuyerForm().fields['uuid'].error_messages['required']))
