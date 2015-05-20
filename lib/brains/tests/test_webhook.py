from django.core.urlresolvers import reverse

from braintree.webhook_notification import WebhookNotification
from braintree.webhook_notification_gateway import WebhookNotificationGateway
from nose.tools import eq_

from lib.brains.tests.base import BraintreeTest


def parsed(**kwargs):
    data = {'kind': 'test', 'subject': ''}
    data.update(kwargs)
    return WebhookNotification(None, data)


def example(**kwargs):
    data = {'bt_signature': 'signature', 'bt_payload': 'payload'}
    data.update(kwargs)
    return data


class TestWebhook(BraintreeTest):
    gateways = {'notify': WebhookNotificationGateway}

    def setUp(self):
        super(TestWebhook, self).setUp()
        self.url = reverse('braintree:webhook')

    def test_allowed(self):
        self.allowed_verbs(self.url, ['get', 'post'])

    def test_get_missing(self):
        eq_(self.client.get(self.url).status_code, 422)

    def test_get_ok(self):
        self.mocks['notify'].verify.return_value = 'foo'
        eq_(self.client.get(self.url + '?bt_challenge=x').json, 'foo')

    def test_post_missing(self):
        eq_(self.client.post(self.url, data={}).status_code, 422)

    def test_post_ok(self):
        self.mocks['notify'].parse.return_value = parsed()
        eq_(self.client.post(self.url, data=example()).status_code, 204)
