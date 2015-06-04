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


def parsed(**kwargs):
    data = {'kind': 'test', 'subject': {}}
    data.update(kwargs)
    return WebhookNotification(None, data)


subscription = {
    'subscription': {
        'id': 'some-bt:id',
        'transactions': [
            {
                'id': 'bt:id',
                'amount': 10,
                'tax_amount': 1,
                'currency_iso_code': 'USD'
            }
        ]
    }
}


def notification(**kwargs):
    data = {
        'kind': 'subscription_charged_successfully',
        'subject': subscription
    }
    data.update(kwargs)
    return data


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
            res.return_value = {'notification': notification()}
            with patch('lib.brains.views.webhook.Processor.process'):
                eq_(self.client.post(self.url, data=example()).status_code,
                    204)


class TestWebhookSubscriptionCharged(BraintreeTest):
    kind = 'subscription_charged_successfully'

    def setUp(self):
        self.buyer, self.braintree_buyer = create_braintree_buyer()
        self.method = create_method(self.braintree_buyer)
        self.seller, self.seller_product = create_seller()
        self.braintree_sub = BraintreeSubscription.objects.create(
            paymethod=self.method,
            seller_product=self.seller_product,
            provider_id='some-bt:id'
        )
        self.sub = subscription

    def test_ok(self):
        Processor(parsed(kind=self.kind, subject=self.sub)).process()
        eq_(Transaction.objects.get().status, constants.STATUS_CHECKED)

    def test_sets(self):
        Processor(parsed(kind=self.kind, subject=self.sub)).process()
        transaction = Transaction.objects.get()
        eq_(transaction.seller, self.seller)
        eq_(transaction.amount, Decimal('10'))
        eq_(transaction.buyer, self.buyer)
        eq_(transaction.currency, 'USD')
        eq_(transaction.provider, constants.PROVIDER_BRAINTREE)
        eq_(transaction.seller_product, self.seller_product)
        eq_(transaction.uid_support, 'bt:id')

    def test_none(self):
        self.braintree_sub.delete()
        obj = Processor(parsed(kind=self.kind, subject=self.sub))
        with self.assertRaises(BraintreeSubscription.DoesNotExist):
            obj.process()
