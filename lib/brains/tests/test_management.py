from django.core.management.base import CommandError

from nose.tools import eq_, raises

from lib.brains.management.commands import braintree_config as config
from lib.brains.tests.base import BraintreeTest


class TestManagement(BraintreeTest):

    def test_created(self):
        seller = config.get_or_create_seller('uuid:concrete')
        same_seller = config.get_or_create_seller('uuid:concrete')
        eq_(seller, same_seller)

    def test_created_product(self):
        seller = config.get_or_create_seller('uuid:concrete')
        seller_product = config.get_or_create_seller_product(
            external_id='some:product:uuid:fxa',
            public_id='some:product',
            seller=seller)
        eq_(seller_product, seller.product.get())

    def get_plans(self):
        self.set_mocks(('GET', 'plans/', 200, 'plans'))
        return config.get_plans()

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
