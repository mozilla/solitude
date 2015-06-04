import base64

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from braintree.webhook_notification import WebhookNotification
from nose.tools import eq_

from lib.brains.tests.base import BraintreeTest


def parsed(**kwargs):
    data = {'kind': 'test', 'subject': ''}
    data.update(kwargs)
    return WebhookNotification(None, data)


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
        eq_(self.client.post(self.url, data=example()).status_code, 204)
