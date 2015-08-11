from datetime import datetime, timedelta
from urllib import urlencode

from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.brains.models import BraintreeTransaction
from lib.brains.tests.base import (
    create_braintree_buyer, create_method, create_seller, create_subscription)
from lib.transactions.models import Transaction
from solitude.base import APITest


class TestBraintreeTransaction(APITest):

    def setUp(self):
        self.buyer, self.braintree_buyer = create_braintree_buyer()
        self.method = create_method(self.braintree_buyer)
        self.seller, self.seller_product = create_seller()
        self.sub = create_subscription(self.method, self.seller_product)
        self.url = reverse('braintree:mozilla:transaction-list')
        self.transaction = Transaction.objects.create(uuid='some:uid',
                                                      buyer=self.buyer)
        super(TestBraintreeTransaction, self).setUp()

    def test_allowed(self):
        self.allowed_verbs(self.url, ['get'])

    def create(self, **attributes):
        final_attributes = dict(
            paymethod=self.method,
            subscription=self.sub,
            transaction=self.transaction,
            billing_period_end_date=datetime.today() + timedelta(days=29),
            billing_period_start_date=datetime.today(),
            kind='sample',
            next_billing_date=datetime.today() + timedelta(days=30),
            next_billing_period_amount='10',
        )
        final_attributes.update(attributes)
        return BraintreeTransaction.objects.create(**final_attributes)

    def get(self, **query):
        return self.client.get('{}?{}'.format(self.url, urlencode(query)))

    def test_get_transaction_by_pk(self):
        obj = self.create()
        eq_(self.client.get(obj.get_uri()).json['resource_pk'], obj.pk)

    def test_filter_by_buyer(self):
        # Create the first transaction:
        trans1 = self.create()

        # Create another transaction:
        gen_buyer2, bt_buyer2 = create_braintree_buyer(braintree_id='bt2')
        gen_trans2 = Transaction.objects.create(uuid='t2', buyer=gen_buyer2)
        paymethod2 = create_method(bt_buyer2)
        trans2 = self.create(paymethod=paymethod2, transaction=gen_trans2)

        objects = self.get(
            transaction__buyer__uuid=self.buyer.uuid).json['objects']
        eq_(len(objects), 1, objects)
        eq_(objects[0]['resource_uri'], trans1.get_uri())

        objects = self.get(
            transaction__buyer__uuid=gen_buyer2.uuid).json['objects']
        eq_(len(objects), 1, objects)
        eq_(objects[0]['resource_uri'], trans2.get_uri())

    def test_only_gets_are_allowed(self):
        obj = self.create()
        self.allowed_verbs(obj.get_uri(), ['get'])
