from datetime import datetime, timedelta

from django.core.urlresolvers import reverse

from nose.tools import eq_

from lib.brains.models import BraintreeTransaction
from lib.brains.tests.base import (
    create_braintree_buyer, create_method, create_seller, create_subscription)
from lib.transactions.models import Transaction
from solitude.base import APITest


class TestBraintreeTransactionrMethod(APITest):

    def setUp(self):
        self.buyer, self.braintree_buyer = create_braintree_buyer()
        self.method = create_method(self.braintree_buyer)
        self.seller, self.seller_product = create_seller()
        self.sub = create_subscription(self.method, self.seller_product)
        self.url = reverse('braintree:mozilla:transaction-list')
        self.transaction = Transaction.objects.create(uuid='some:uid')
        super(TestBraintreeTransactionrMethod, self).setUp()

    def test_allowed(self):
        self.allowed_verbs(self.url, ['get'])

    def create(self):
        return BraintreeTransaction.objects.create(
            paymethod=self.method,
            subscription=self.sub,
            transaction=self.transaction,
            billing_period_end_date=datetime.today() + timedelta(days=29),
            billing_period_start_date=datetime.today(),
            kind='sample',
            next_billing_date=datetime.today() + timedelta(days=30),
            next_billing_period_amount='10'
        )

    def test_get(self):
        obj = self.create()
        eq_(self.client.get(obj.get_uri()).json['resource_pk'], obj.pk)

    def test_no_patch(self):
        obj = self.create()
        self.allowed_verbs(obj.get_uri(), ['get'])
