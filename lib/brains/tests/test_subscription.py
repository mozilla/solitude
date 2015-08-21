from datetime import datetime

from django.core.urlresolvers import reverse

import mock
from braintree.subscription import Subscription
from braintree.subscription_gateway import SubscriptionGateway
from braintree.successful_result import SuccessfulResult
from nose.tools import eq_, ok_

from lib.brains.models import BraintreeSubscription
from lib.brains.tests.base import (
    BraintreeTest, create_braintree_buyer, create_method, create_seller, error)


def method(**kw):
    method = {
        'id': 'some:id',
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }
    method.update(**kw)
    return Subscription(None, method)


def successful_subscription(**kw):
    return SuccessfulResult({'subscription': method(**kw)})


def create_method_all():
    buyer, braintree_buyer = create_braintree_buyer()
    seller, seller_product = create_seller()
    method = create_method(braintree_buyer)
    return method, seller_product


class TestSubscription(BraintreeTest):
    gateways = {'sub': SubscriptionGateway}

    def setUp(self):
        super(TestSubscription, self).setUp()
        self.url = reverse('braintree:subscription')

    def test_allowed(self):
        self.allowed_verbs(self.url, ['post'])

    def test_ok(self):
        self.mocks['sub'].create.return_value = successful_subscription()

        method, seller_product = create_method_all()
        res = self.client.post(
            self.url, data={
                'paymethod': method.get_uri(),
                'plan': 'moz-brick'
            })

        data = {
            'payment_method_token': mock.ANY,
            'plan_id': 'moz-brick',
            'descriptor': {
                'name': 'Mozilla*Product',
                'url': 'mozilla.org'
            },
            'trial_period': False,
        }
        self.mocks['sub'].create.assert_called_with(data)

        eq_(res.status_code, 201)
        subscription = BraintreeSubscription.objects.get()
        eq_(subscription.provider_id, 'some:id')

    def test_no_method(self):
        method, seller_product = create_method_all()
        res = self.client.post(
            self.url,
            data={
                'method': method.get_uri() + 'n',
                'plan': 'moz-brick'
            })

        eq_(res.status_code, 422, res.content)

    def test_no_plan(self):
        method, seller_product = create_method_all()
        res = self.client.post(
            self.url, data={'paymethod': method.get_uri(), 'plan': 'nope'})

        eq_(res.status_code, 422, res.content)
        eq_(self.mozilla_error(res.json, 'plan'), ['does_not_exist'])

    def test_braintree_fails(self):
        self.mocks['sub'].create.return_value = error([{
            'attribute': 'payment_method_token',
            'message': 'Payment method token is invalid.',
            'code': '91903'
        }])

        method, seller_product = create_method_all()
        res = self.client.post(
            self.url, data={
                'paymethod': method.get_uri(),
                'plan': 'moz-brick'
            })

        ok_(not BraintreeSubscription.objects.exists())
        eq_(res.status_code, 422, res.content)
        eq_(self.braintree_error(res.json, 'payment_method_token'), ['91903'])


class TestSubscriptionChange(BraintreeTest):
    gateways = {'sub': SubscriptionGateway}

    def setUp(self):
        super(TestSubscriptionChange, self).setUp()
        self.url = reverse('braintree:subscription.change')

    def create_subscription_methods(self):
        self.first_method, product = create_method_all()
        self.second_method = create_method(self.first_method.braintree_buyer)
        return BraintreeSubscription.objects.create(
            paymethod=self.first_method, seller_product=product)

    def test_change(self):
        self.mocks['sub'].update.return_value = successful_subscription()

        sub = self.create_subscription_methods()
        res = self.client.post(self.url, data={
            'paymethod': self.second_method.get_uri(),
            'subscription': sub.get_uri()
        })
        eq_(res.status_code, 200, res.content)
        eq_(sub.reget().paymethod.pk, self.second_method.pk)

        self.mocks['sub'].update.assert_called_with(
            sub.provider_id,
            {'payment_method_token': self.second_method.provider_id})

    def test_inactive_subscription(self):
        sub = self.create_subscription_methods()
        sub.active = False
        sub.save()

        res = self.client.post(self.url, data={
            'paymethod': self.second_method.get_uri(),
            'subscription': sub.get_uri()
        })
        eq_(res.status_code, 422, res.content)

    def test_inactive_method(self):
        sub = self.create_subscription_methods()
        self.second_method.active = False
        self.second_method.save()

        res = self.client.post(self.url, data={
            'paymethod': self.second_method.get_uri(),
            'subscription': sub.get_uri()
        })
        eq_(res.status_code, 422, res.content)

    def test_error(self):
        self.mocks['sub'].update.return_value = error()

        sub = self.create_subscription_methods()
        res = self.client.post(self.url, data={
            'paymethod': self.second_method.get_uri(),
            'subscription': sub.get_uri()
        })
        eq_(res.status_code, 422, res.content)
        eq_(sub.reget().paymethod.pk, self.first_method.pk)


class TestSubscriptionCancel(BraintreeTest):
    gateways = {'sub': SubscriptionGateway}

    def setUp(self):
        super(TestSubscriptionCancel, self).setUp()
        self.url = reverse('braintree:subscription.cancel')

    def test_allowed(self):
        self.allowed_verbs(self.url, ['post'])

    def create_subscription(self):
        method, product = create_method_all()
        return BraintreeSubscription.objects.create(
            paymethod=method, seller_product=product)

    def post(self, obj, **kw):
        data = {'subscription': obj.get_uri()}
        data.update(**kw)
        return self.client.post(self.url, data=data)

    def test_post(self):
        self.mocks['sub'].cancel.return_value = successful_subscription()

        obj = self.create_subscription()
        res = self.post(obj)
        eq_(res.status_code, 200, res.status_code)

        self.mocks['sub'].cancel.assert_called_with(obj.provider_id)

    def test_fails_post(self):
        self.mocks['sub'].cancel.return_value = error()

        obj = self.create_subscription()
        res = self.post(obj)
        eq_(res.status_code, 422, res.content)
        eq_(obj.reget().active, True)

        self.mocks['sub'].cancel.assert_called_with(obj.provider_id)

    def test_cancel_inactive(self):
        obj = self.create_subscription()
        obj.active = False
        obj.save()

        res = self.post(obj)
        eq_(res.status_code, 422, res.content)


class TestSubscriptionViewSet(BraintreeTest):
    gateways = {'sub': SubscriptionGateway}

    def setUp(self):
        self.buyer, self.braintree_buyer = create_braintree_buyer()
        self.method = create_method(self.braintree_buyer)
        self.seller, self.seller_product = create_seller()
        self.url = reverse('braintree:mozilla:subscription-list')
        super(TestSubscriptionViewSet, self).setUp()

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

    def test_patch_read_only(self):
        obj = self.create()

        paymethod = create_method(self.braintree_buyer)
        seller, seller_product = create_seller(
            seller_product_data={'public_id': 'a-different-brick'})

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
                {'active': 1},
                {'paymethod': self.method.pk},
                {'seller_product': self.seller_product.pk},
                {'paymethod__braintree_buyer': self.method.braintree_buyer.pk},
                {'paymethod__braintree_buyer__buyer':
                 self.method.braintree_buyer.buyer.pk},
                {'provider_id': 'some:id'},
        ):
            res = self.client.get(self.url, d)
            eq_(res.status_code, 200, res.content)
            eq_(res.json['meta']['total_count'], 1, d)
            eq_(res.json['objects'][0]['resource_pk'], obj.pk)
