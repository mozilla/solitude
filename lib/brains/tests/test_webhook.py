import base64
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from braintree.webhook_notification import WebhookNotification
from mock import patch
from nose.tools import eq_

from lib.brains.models import BraintreeSubscription, BraintreeTransaction
from lib.brains.serializers import serialize_webhook
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
        'next_billing_date': datetime.today() + timedelta(days=30),
        'next_billing_period_amount': 10,
        'billing_period_end_date': datetime.today() + timedelta(days=29),
        'billing_period_start_date': datetime.today(),
        'price': 10
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


@override_settings(BRAINTREE_PROXY='http://m.o')
class TestWebhookWithSubscription(SubscriptionTest):

    def setUp(self):
        super(TestWebhookWithSubscription, self).setUp()
        self.url = reverse('braintree:webhook')
        self.patch_webhook_forms()
        self.req.post.return_value = self.get_response('foo', 204)

    def test_post_ok(self):
        with patch('lib.brains.views.webhook.XmlUtil.dict_from_xml') as attr:
            attr.return_value = {
                'notification': {
                    'kind': 'subscription_charged_successfully',
                    'subject': subscription()
                }
            }
            res = self.client.post(self.url, data=example())
            eq_(res.status_code, 200)
            eq_(res.json.keys(), ['mozilla', 'braintree'])

    def test_post_ignored(self):
        with patch('lib.brains.views.webhook.XmlUtil.dict_from_xml') as attr:
            attr.return_value = {
                'notification': {
                    'kind': '',
                    'subject': ''
                }
            }
            res = self.client.post(self.url, data=example())
            eq_(res.status_code, 204)


class TestSubscription(SubscriptionTest):
    kind = 'subscription_charged_successfully'

    def process(self, subscription):
        hook = Processor(notification(subject=subscription, kind=self.kind))
        hook.process()
        hook.update_transactions(self.braintree_sub)
        return hook

    def test_data(self):
        hook = self.process(subscription())
        eq_(hook.data['braintree']['kind'],
            'subscription_charged_successfully')
        eq_(hook.data['mozilla']['buyer']['resource_pk'], self.buyer.pk)
        eq_(hook.data['mozilla']['transaction']['generic']['resource_pk'],
            Transaction.objects.get().pk)
        eq_(hook.data['mozilla']['transaction']['braintree']['resource_pk'],
            BraintreeTransaction.objects.get().pk)
        eq_(hook.data['mozilla']['paymethod']['resource_pk'], self.method.pk)
        eq_(hook.data['mozilla']['product']['resource_pk'],
            self.seller_product.pk)
        eq_(hook.data['mozilla']['subscription']['resource_pk'],
            self.braintree_sub.pk)

    def test_no_transactions(self):
        process = Processor(notification(
            subject=subscription(transactions=[]), kind=self.kind))
        process.process()
        eq_(process.transactions, [])

    def test_no_transactions_data(self):
        process = Processor(notification(
            subject=subscription(transactions=[]), kind=self.kind))
        process.process()
        eq_(process.transaction, None)

    def test_transactions_order(self):
        process = Processor(notification(
            subject=subscription(transactions=[
                # Repeated transactions only most recent (first)
                # should be used.
                transaction(id='first:id'),
                transaction(id='another:id')
            ]),
            kind=self.kind))
        process.process()

        eq_(process.transactions[0].uid_support, 'first:id')

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

    def test_submitted_caught(self):
        sub = subscription(
            transactions=[transaction(status='submitted_for_settlement')])
        self.process(sub)
        trans = Transaction.objects.get()
        eq_(trans.status, constants.STATUS_CHECKED)

    def test_braintree_transaction(self):
        sub = subscription(transactions=[transaction(status='settled')])
        self.process(sub)
        trans = Transaction.objects.get()
        brains = trans.braintreetransaction
        eq_(brains.kind, self.kind)
        eq_(brains.transaction, trans)
        eq_(brains.paymethod, self.method)
        eq_(brains.subscription, self.braintree_sub)
        eq_(brains.next_billing_period_amount, Decimal('10.00'))

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

    def test_cant_serialize(self):
        trans = Transaction.objects.create(provider=constants.PROVIDER_BANGO)
        with self.assertRaises(ValueError):
            serialize_webhook(None, trans)


class TestWebhookSubscriptionCharged(SubscriptionTest):
    kind = 'subscription_charged_successfully'

    def test_ok(self):
        Processor(notification(kind=self.kind, subject=self.sub)).process()
        transaction = Transaction.objects.get()
        eq_(transaction.status, constants.STATUS_CHECKED)
        eq_(BraintreeTransaction.objects.get().transaction, transaction)
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


class TestWebhookSubscriptionNotCharged(SubscriptionTest):
    kind = 'subscription_charged_unsuccessfully'

    def test_ok(self):
        sub = subscription(transactions=
            [transaction(status='processor_declined',
                         processor_response_code='nah')])
        Processor(notification(kind=self.kind, subject=sub)).process()
        eq_(Transaction.objects.get().status, constants.STATUS_FAILED)


class TestWebhookSubscriptionCancelled(SubscriptionTest):
    kind = 'subscription_cancelled'

    def test_ok(self):
        Processor(notification(kind=self.kind, subject=self.sub)).process()
        eq_(Transaction.objects.get().status, constants.STATUS_CHECKED)

    def test_subscription_inactive(self):
        Processor(notification(kind=self.kind, subject=self.sub)).process()
        eq_(self.braintree_sub.reget().active, False)
