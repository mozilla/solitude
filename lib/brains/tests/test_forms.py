from django.test.utils import override_settings

from nose.tools import eq_

from lib.brains.forms import (
    SaleForm, SubscriptionCancelForm, SubscriptionForm, SubscriptionUpdateForm,
    WebhookParseForm, WebhookVerifyForm)
from lib.brains.tests.base import (
    BraintreeTest, create_braintree_buyer, create_method, create_seller)


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


class TestSubscriptionManagement(BraintreeTest):

    def test_missing_update_params(self):
        form = SubscriptionUpdateForm({})
        form.is_valid()
        errors = form.errors
        # Make sure empty params are caught.
        assert 'subscription' in errors, errors.as_text()
        assert 'paymethod' in errors, errors.as_text()

    def test_missing_cancel_params(self):
        form = SubscriptionCancelForm({})
        form.is_valid()
        errors = form.errors
        # Make sure empty params are caught.
        assert 'subscription' in errors, errors.as_text()


class TestSaleForm(BraintreeTest):

    def process(self, data):
        form = SaleForm(data)
        form.is_valid()
        return form, form.errors

    def test_no_paymethod_nonce(self):
        form, errors = self.process({})
        assert '__all__' in errors, errors.as_text()

    def test_both_paymethod_nonce(self):
        method = create_method(create_braintree_buyer()[1])
        form, errors = self.process({
            'nonce': 'abc',
            'paymethod': method.get_uri()
        })
        assert '__all__' in errors, errors.as_text()

    def test_paymethod_does_not_exist(self):
        form, errors = self.process({'paymethod': '/nope'})
        assert 'paymethod' in errors, errors.as_text()

    def test_no_product(self):
        form, errors = self.process({
            'amount': '5',
            'nonce': 'noncey',
            'product_id': 'nope',
        })
        assert 'product_id' in errors, errors.as_text()

    def test_ok(self):
        seller, seller_product = create_seller()
        form, errors = self.process({
            'amount': '5',
            'nonce': 'noncey',
            'product_id': seller_product.public_id
        })
        assert not errors, errors.as_text()
        assert 'payment_method_token' not in form.braintree_data
        eq_(form.braintree_data['payment_method_nonce'], 'noncey')

    def test_ok_method(self):
        seller, seller_product = create_seller()
        method = create_method(create_braintree_buyer()[1])
        form, errors = self.process({
            'amount': '5',
            'paymethod': method.get_uri(),
            'product_id': seller_product.public_id
        })
        assert not errors, errors.as_text()
        assert 'payment_method_nonce' not in form.braintree_data
        eq_(form.braintree_data['payment_method_token'], method.provider_id)
