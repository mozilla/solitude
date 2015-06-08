import base64
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from braintree.webhook_notification import WebhookNotification
from mock import patch
from nose.tools import eq_

from lib.brains.models import BraintreeSubscription
from lib.brains.tests.base import (
    BraintreeTest, create_braintree_buyer, create_method, create_seller)
from lib.brains.webhooks import Processor
from lib.transactions import constants
from lib.transactions.models import Transaction


def notification(**kwargs):
    data = {
        'kind': 'test',
        'subject': {}
    }
    data.update(kwargs)
    return WebhookNotification(None, data)


def transaction(**kwargs):
    data = {
        'id': 'bt:id',
        'amount': 10,
        'tax_amount': 1,
        'currency_iso_code': 'USD',
        'status': 'settled'
    }
    data.update(kwargs)
    return data


def subscription(**kwargs):
    data = {
        'id': 'some-bt:id',
        'transactions': [transaction()],
    }
    data.update(kwargs)
    return {'subscription': data}


example_xml = """<?xml version="1.0" encoding="UTF-8"?>
<notification>
    <kind>subscription_charged_successfully</kind>
    <subject></subject>
</notification>
"""


def example(**kwargs):
    data = {
        'bt_signature': 'signature',
        'bt_payload': base64.encodestring(str(example_xml))
    }
    data.update(kwargs)
    return data


@override_settings(BRAINTREE_PROXY='http://m.o')
class TestWebhook(BraintreeTest):

    def setUp(self):
        super(TestWebhook, self).setUp()
        self.url = reverse('braintree:webhook')
        self.patch_webhook_forms()

    def test_allowed(self):
        self.allowed_verbs(self.url, ['get', 'post'])

    def test_get_missing(self):
        eq_(self.client.get(self.url).status_code, 422)

    def test_get_ok(self):
        self.req.get.return_value = self.get_response('foo', 200)
        eq_(self.client.get(self.url + '?bt_challenge=x').json, 'foo')

    def test_post_missing(self):
        eq_(self.client.post(self.url, data={}).status_code, 422)

    def test_post_auth_fails(self):
        self.req.post.return_value = self.get_response('', 403)
        eq_(self.client.post(self.url, data=example()).status_code, 422)

    def test_post_ok(self):
        self.req.post.return_value = self.get_response('foo', 204)
        with patch('lib.brains.views.webhook.XmlUtil.dict_from_xml') as res:
            res.return_value = {
                'notification': {'kind': '', 'subject': subscription()}}
            with patch('lib.brains.views.webhook.Processor.process'):
                eq_(self.client.post(self.url, data=example()).status_code,
                    204)


class SubscriptionTest(BraintreeTest):

    def setUp(self):
        self.buyer, self.braintree_buyer = create_braintree_buyer()
        self.method = create_method(self.braintree_buyer)
        self.seller, self.seller_product = create_seller()
        self.braintree_sub = BraintreeSubscription.objects.create(
            paymethod=self.method,
            seller_product=self.seller_product,
            provider_id='some-bt:id'
        )
        self.sub = subscription(id='some-bt:id')


class TestSubscription(SubscriptionTest):

    def process(self, subscription):
        process = Processor(notification(subject=subscription))
        process.update_transactions(process.webhook.subscription,
                                    self.braintree_sub)

    def test_flip(self):
        process = Processor(notification(subject=subscription()))
        process.update_subscription(self.braintree_sub, True)
        eq_(self.braintree_sub.reget().active, True)
        process.update_subscription(self.braintree_sub, False)
        eq_(self.braintree_sub.reget().active, False)

    def test_ignored(self):
        sub = subscription(transactions=[transaction(status='settling')])
        self.process(sub)
        eq_(Transaction.objects.count(), 0)

    def test_caught(self):
        sub = subscription(transactions=[transaction(status='settled')])
        self.process(sub)
        trans = Transaction.objects.get()
        eq_(trans.status, constants.STATUS_CHECKED)
        eq_(trans.seller, self.seller)
        eq_(trans.amount, Decimal('10'))
        eq_(trans.buyer, self.buyer)
        eq_(trans.currency, 'USD')
        eq_(trans.provider, constants.PROVIDER_BRAINTREE)
        eq_(trans.seller_product, self.seller_product)
        eq_(trans.uid_support, 'bt:id')

    def test_processor_declined(self):
        sub = subscription(transactions=[
            transaction(status='processor_declined',
                        processor_response_code='wat'),
        ])
        self.process(sub)
        trans = Transaction.objects.get()
        eq_(trans.status, constants.STATUS_FAILED)
        eq_(trans.status_reason, 'processor_declined wat')

    def test_settlement_declined(self):
        sub = subscription(transactions=[
            transaction(status='settlement_declined',
                        processor_settlement_response_code='wat'),
        ])
        self.process(sub)
        trans = Transaction.objects.get()
        eq_(trans.status, constants.STATUS_FAILED)
        eq_(trans.status_reason, 'settlement_declined wat')

    def test_gateway_rejected(self):
        sub = subscription(transactions=[
            transaction(status='gateway_rejected',
                        gateway_rejection_reason='wat'),
        ])
        self.process(sub)
        trans = Transaction.objects.get()
        eq_(trans.status, constants.STATUS_FAILED)
        eq_(trans.status_reason, 'gateway_rejected wat')

    def test_repeated(self):
        sub = subscription(transactions=[transaction(status='settled')])
        self.process(sub)
        self.process(sub)
        eq_(Transaction.objects.count(), 1)

    def test_repeated_but_changed_status(self):
        sub = subscription(transactions=[transaction(status='settled')])
        self.process(sub)
        sub = subscription(transactions=[
            transaction(status='processor_declined',
                        processor_response_code='wat')
        ])
        with self.assertRaises(ValueError):
            self.process(sub)


class TestWebhookSubscriptionCharged(SubscriptionTest):
    kind = 'subscription_charged_successfully'

    def test_ok(self):
        Processor(notification(kind=self.kind, subject=self.sub)).process()
        eq_(Transaction.objects.get().status, constants.STATUS_CHECKED)
        eq_(self.braintree_sub.reget().active, True)

    def test_subscription_active(self):
        self.braintree_sub.active = False
        self.braintree_sub.save()
        Processor(notification(kind=self.kind, subject=self.sub)).process()
        eq_(self.braintree_sub.reget().active, True)

    def test_none(self):
        self.braintree_sub.delete()
        obj = Processor(notification(kind=self.kind, subject=self.sub))
        with self.assertRaises(BraintreeSubscription.DoesNotExist):
            obj.process()


class TestWebhookSubscriptionCancelled(SubscriptionTest):
    kind = 'subscription_cancelled'

    def test_ok(self):
        Processor(notification(kind=self.kind, subject=self.sub)).process()
        eq_(Transaction.objects.get().status, constants.STATUS_CHECKED)

    def test_subscription_inactive(self):
        Processor(notification(kind=self.kind, subject=self.sub)).process()
        eq_(self.braintree_sub.reget().active, False)
