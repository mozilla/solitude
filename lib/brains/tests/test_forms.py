from django.test.utils import override_settings

from nose.tools import eq_

from lib.brains.forms import (
    SubscriptionForm, WebhookParseForm, WebhookVerifyForm)
from lib.brains.tests.base import BraintreeTest


@override_settings(BRAINTREE_PROXY='http://m.o')
class TestWebhook(BraintreeTest):

    def setUp(self):
        self.patch_webhook_forms()

    def test_verify_fails(self):
        self.req.get.return_value = self.get_response('nope', 403)
        form = WebhookVerifyForm({'bt_challenge': 'f'})
        assert not form.is_valid()

    def test_verify_ok(self):
        self.req.get.return_value = self.get_response('f', 200)
        form = WebhookVerifyForm({'bt_challenge': 'b'})

        assert form.is_valid()
        eq_(form.response, 'f')
        self.req.get.assert_called_with(
            'http://m.o/verify', params={'bt_challenge': 'b'})

    def test_parse_fails(self):
        self.req.post.return_value = self.get_response('nope', 403)
        form = WebhookParseForm({'bt_payload': 'p', 'bt_signature': 's'})
        assert not form.is_valid()

    def test_parse_not_204(self):
        self.req.post.return_value = self.get_response('something', 200)
        form = WebhookParseForm({'bt_payload': 'p', 'bt_signature': 's'})
        assert not form.is_valid()

    def test_parse_ok(self):
        self.req.post.return_value = self.get_response('', 204)
        form = WebhookParseForm({'bt_payload': 'p', 'bt_signature': 's'})

        assert form.is_valid()
        self.req.post.assert_called_with(
            'http://m.o/parse',
            {'bt_signature': 's', 'bt_payload': 'p'}
        )


class TestSubscription(BraintreeTest):

    def setUp(self):
        self.form = SubscriptionForm()

    def test_default_name(self):
        eq_(self.form.get_name('not-brick'), 'Product')

    def test_seller_name(self):
        eq_(self.form.get_name('mozilla-concrete-brick'), 'Brick')

    def test_format_descriptor(self):
        for in_string, out_string in [
                ('Product', 'Mozilla*Product'),
                ('Long Product With Space', 'Mozilla*Long Product W')
            ]:
            eq_(self.form.format_descriptor(in_string), out_string)
