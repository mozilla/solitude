from braintree.payment_method_gateway import PaymentMethodGateway
from braintree.subscription_gateway import SubscriptionGateway
from nose.tools import eq_

from lib.brains.tests.base import BraintreeTest, create_subscription
from lib.brains.tests.test_paymethod import successful_method
from lib.brains.tests.test_subscription import (
    create_method_all, successful_subscription)


class TestClose(BraintreeTest):
    gateways = {
        'pay': PaymentMethodGateway,
        'sub': SubscriptionGateway,
    }

    def setUp(self):
        super(TestClose, self).setUp()
        self.method, self.product = create_method_all()
        self.buyer = self.method.braintree_buyer.buyer
        self.sub = create_subscription(self.method, self.product)

    def test_no_buyer(self):
        self.buyer.delete()
        self.buyer.close()

    def test_close(self):
        self.mocks['pay'].delete.return_value = successful_method()
        self.mocks['sub'].cancel.return_value = successful_subscription()

        self.buyer.close()

        self.mocks['pay'].delete.assert_called_with(self.method.provider_id)
        self.mocks['sub'].cancel.assert_called_with(self.sub.provider_id)

        eq_(self.method.reget().active, False)
        eq_(self.sub.reget().active, False)

    def test_listens_signal(self):
        self.mocks['pay'].delete.return_value = successful_method()
        self.mocks['sub'].cancel.return_value = successful_subscription()

        self.buyer.close_signal.send(
            buyer=self.buyer, sender=self.buyer.__class__)

    def test_inactive_method(self):
        # If a method is inactive, then we still go and call cancel on
        # the subscription, just in case solitude is out of sync.
        self.method.active = False
        self.method.save()
        self.mocks['sub'].cancel.return_value = successful_subscription()

        self.buyer.close()

        self.mocks['sub'].cancel.assert_called_with(self.sub.provider_id)

    def test_inactive_subscription(self):
        self.sub.active = False
        self.sub.save()

        self.mocks['pay'].delete.return_value = successful_method()

        self.buyer.close()
        # self.mocks['sub'] not called, no need test the BraintreeTest
        # setup deals with this.
