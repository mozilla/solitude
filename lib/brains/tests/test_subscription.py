from datetime import datetime

from django.core.urlresolvers import reverse

import mock
from braintree.subscription import Subscription
from braintree.subscription_gateway import SubscriptionGateway
from braintree.successful_result import SuccessfulResult
from nose.tools import eq_

from lib.brains.models import BraintreeSubscription
from lib.brains.tests.base import (
    BraintreeTest, create_braintree_buyer, create_method, create_seller, error)
from solitude.base import APITest


def method(**kw):
    method = {
        'id': 'some:id',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }
    method.update(**kw)
    return Subscription(None, method)


def successful_method(**kw):
    return SuccessfulResult({'subscription': method(**kw)})


class TestSubscriptionMethod(BraintreeTest):
    gateways = {'sub': SubscriptionGateway}

    def setUp(self):
        super(TestSubscriptionMethod, self).setUp()
        self.url = reverse('braintree:subscription')

    def test_allowed(self):
        self.allowed_verbs(self.url, ['post'])

    def create(self):
        buyer, braintree_buyer = create_braintree_buyer()
        seller, seller_product = create_seller()
        method = create_method(braintree_buyer)
        return method

    def test_ok(self):
        self.mocks['sub'].create.return_value = successful_method()

        method = self.create()
        res = self.client.post(
            self.url, data={'paymethod': method.get_uri(), 'plan': 'brick'})

        data = {
            'payment_method_token': mock.ANY,
            'plan_id': 'brick',
            'name': 'Mozilla',
            'trial_period': False,
        }
        self.mocks['sub'].create.assert_called_with(data)

        eq_(res.status_code, 201)
        subscription = BraintreeSubscription.objects.get()
        eq_(subscription.provider_id, 'some:id')

    def test_no_method(self):
        method = self.create()
        res = self.client.post(
            self.url, data={'method': method.get_uri() + 'n', 'plan': 'brick'})

        eq_(res.status_code, 400, res.content)

    def test_no_plan(self):
        method = self.create()
        res = self.client.post(
            self.url, data={'paymethod': method.get_uri(), 'plan': 'nope'})

        eq_(res.status_code, 400, res.content)

    def test_braintree_fails(self):
        self.mocks['sub'].create.return_value = error()

        method = self.create()
        res = self.client.post(
            self.url, data={'paymethod': method.get_uri(), 'plan': 'brick'})

        eq_(res.status_code, 400, res.content)


class TestSubscriptionViewSet(APITest):

    def setUp(self):
        self.buyer, self.braintree_buyer = create_braintree_buyer()
        self.method = create_method(self.braintree_buyer)
        self.seller, self.seller_product = create_seller()
        self.url = reverse('braintree:mozilla:subscription-list')
        super(self.__class__, self).setUp()

    def test_allowed(self):
        self.allowed_verbs(self.url, ['get'])

    def create(self):
        return BraintreeSubscription.objects.create(
            paymethod=self.method,
            seller_product=self.seller_product,
            provider_id='some:id')

    def test_get(self):
        obj = self.create()
        eq_(self.client.get(obj.get_uri()).json['resource_pk'], obj.pk)

    def test_patch(self):
        obj = self.create()
        res = self.client.patch(obj.get_uri(), data={'active': False})
        eq_(res.status_code, 200, res.content)
        eq_(self.client.get(obj.get_uri()).json['active'], False)

    def test_patch_read_only(self):
        obj = self.create()

        paymethod = create_method(self.braintree_buyer)
        seller, seller_product = create_seller()

        data = {
            'paymethod': paymethod.get_uri(),
            'seller_product': seller_product.get_uri(),
            'provider_id': 'different:id',
        }

        res = self.client.patch(obj.get_uri(), data=data)
        eq_(res.status_code, 200, res.content)

        res = self.client.get(obj.get_uri())
        eq_(res.json['paymethod'], self.method.get_uri())
        eq_(res.json['seller_product'], self.seller_product.get_uri())
        eq_(res.json['provider_id'], 'some:id')

    def test_queries(self):
        obj = self.create()
        for d in (
                {'paymethod': self.method.pk},
                {'seller_product': self.seller_product.pk},
                {'paymethod__braintree_buyer': self.method.braintree_buyer.pk},
                {'paymethod__braintree_buyer__buyer':
                 self.method.braintree_buyer.buyer.pk},

        ):
            res = self.client.get(self.url, d)
            eq_(res.json['meta']['total_count'], 1)
            eq_(res.json['objects'][0]['resource_pk'], obj.pk)
