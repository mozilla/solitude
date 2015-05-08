from datetime import datetime

from django.core.urlresolvers import reverse

from braintree.customer import Customer
from braintree.customer_gateway import CustomerGateway
from braintree.error_result import ErrorResult
from braintree.successful_result import SuccessfulResult
from nose.tools import eq_, ok_

from lib.brains.forms import BuyerForm
from lib.brains.models import BraintreeBuyer
from lib.brains.tests.base import (
    BraintreeTest, create_braintree_buyer, create_buyer)


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

    def test_buyer_doesnt_exist(self):
        res = self.client.post(self.url, data={'uuid': 'nope'})
        eq_(res.status_code, 400)

    def test_braintree_buyer_exists(self):
        buyer, braintree_buyer = create_braintree_buyer()
        res = self.client.post(self.url, data={'uuid': buyer.uuid})
        eq_(res.status_code, 400)

    def test_ok(self):
        self.mocks['customer'].create.return_value = successful_customer()

        buyer = create_buyer()
        res = self.client.post(self.url, data={'uuid': buyer.uuid})
        eq_(res.status_code, 201)

        braintree_buyer = BraintreeBuyer.objects.get()
        eq_(res.json['mozilla']['resource_pk'], braintree_buyer.pk)
        eq_(res.json['mozilla']['braintree_id'], 'customer-id')
        eq_(res.json['braintree']['id'], 'customer-id')

    def test_error(self):
        self.mocks['customer'].create.return_value = error()

        buyer = create_buyer()
        res = self.client.post(self.url, data={'uuid': buyer.uuid})

        ok_(not BraintreeBuyer.objects.exists())
        eq_(res.status_code, 400)

    def test_no_uuid(self):
        res = self.client.post(self.url, data={})
        eq_(res.status_code, 400)
        eq_(res.json['uuid'][0],
            unicode(BuyerForm().fields['uuid'].error_messages['required']))
