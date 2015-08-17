from django.core.management.base import CommandError

from braintree.plan import Plan
from braintree.plan_gateway import PlanGateway
from nose.tools import eq_, raises

from lib.brains.client import get_client
from lib.brains.management.commands import braintree_config as config
from lib.brains.tests.base import BraintreeTest


class TestManagement(BraintreeTest):
    gateways = {'plans': PlanGateway}

    def test_created(self):
        seller = config.get_or_create_seller('uuid:fxa')
        same_seller = config.get_or_create_seller('uuid:fxa')
        eq_(seller, same_seller)

    def test_created_product(self):
        seller = config.get_or_create_seller('uuid:fxa')
        seller_product = config.get_or_create_seller_product(
            external_id='some:product:uuid:concrete',
            public_id='some:product',
            seller=seller)
        eq_(seller_product, seller.product.get())

    def get_plans(self, plan=None):
        # Note price is a string not a decimal or something useful:
        # https://github.com/braintree/braintree_python/issues/52
        plans = [
            Plan(None, {
                'billing_day_of_month': None,
                'id': 'mozilla-concrete-mortar',
                'price': '1',
                'trial_period': None
            }),
            Plan(None, {
                'billing_day_of_month': None,
                'id': 'mozilla-concrete-brick',
                'price': '10',
                'trial_period': None
            })
        ]
        if plan:
            plans.append(plan)
        self.mocks['plans'].all.return_value = plans
        return config.get_plans(get_client())

    def test_plans(self):
        eq_(self.get_plans().keys(),
            [u'mozilla-concrete-mortar', u'mozilla-concrete-brick'])

    @raises(CommandError)
    def test_product_missing(self):
        config.product_exists(self.get_plans(), 'nope', 1)

    @raises(CommandError)
    def test_price_wrong(self):
        config.product_exists(self.get_plans(), 'mozilla-concrete-brick', 1)

    def test_plan_ok(self):
        config.product_exists(self.get_plans(), 'mozilla-concrete-brick', 10)

    @raises(CommandError)
    def test_trial_period(self):
        plan = Plan(None, {
            'billing_day_of_month': None,
            'id': 'trial',
            'price': '1',
            'trial_period': '1'
        })
        config.product_exists(self.get_plans(plan), 'trial', 1)

    @raises(CommandError)
    def test_billing_day_of_month(self):
        plan = Plan(None, {
            'billing_day_of_month': 1,
            'id': 'day',
            'price': '1',
            'trial_period': None
        })
        config.product_exists(self.get_plans(plan), 'day', 1)
