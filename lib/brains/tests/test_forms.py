from django.test.utils import override_settings

from braintree.subscription_gateway import SubscriptionGateway
from nose.tools import eq_

from lib.brains.forms import (
    SaleForm, SubscriptionCancelForm, SubscriptionForm, SubscriptionUpdateForm,
    WebhookParseForm, WebhookVerifyForm)
from lib.brains.tests.base import (
    BraintreeTest, create_braintree_buyer, create_method, create_seller,
    ProductsTest)

from .test_subscription import create_method_all


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


class TestSubscription(BraintreeTest, ProductsTest):
    gateways = {'sub': SubscriptionGateway}

    def setUp(self):
        super(TestSubscription, self).setUp()
        self.paymethod, seller_product = create_method_all()

    def submit(self, expect_errors=False, data=None):
        if not data:
            data = {}
        submission = {
            'paymethod': self.paymethod.get_uri(),
            'plan_id': 'moz-brick',
        }
        submission.update(data)
        form = SubscriptionForm(submission)
        if not expect_errors:
            assert form.is_valid(), form.errors.as_text()
        return form

    def test_seller_name(self):
        eq_(SubscriptionForm().get_name('moz-brick'), 'Recurring')

    def test_plan_is_not_a_seller_product(self):
        form = self.submit(data={'plan': 'no-seller-product'},
                           expect_errors=True)

        assert 'plan' in form.errors, form.errors.as_text()

    def test_plan_is_not_a_configured_product(self):
        seller, prod = create_seller(seller_product_data={
            'public_id': 'plan-id-not-in-config',
        })
        form = self.submit(expect_errors=True,
                           data={'plan': prod.public_id})
        assert 'plan' in form.errors, form.errors.as_text()

    def test_format_descriptor(self):
        for in_string, out_string in [
            ('Product', 'Mozilla*Product'),
            ('Long Product With Space', 'Mozilla*Long Product W')
        ]:
            eq_(SubscriptionForm().format_descriptor(in_string), out_string)


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


class TestSaleForm(BraintreeTest, ProductsTest):

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
            'amount': '10.00',
            'nonce': 'noncey',
            'product_id': 'nope',
        })
        assert 'product_id' in errors, errors.as_text()

    def test_ok(self):
        seller, seller_product = create_seller()
        self.product_mock.get('moz-brick').recurrence = None

        form, errors = self.process({
            'amount': '10.00',
            'nonce': 'noncey',
            'product_id': seller_product.public_id
        })
        assert not errors, errors.as_text()
        assert 'payment_method_token' not in form.braintree_data
        eq_(form.braintree_data['payment_method_nonce'], 'noncey')

    def test_ok_method(self):
        seller, seller_product = create_seller()
        self.product_mock.get('moz-brick').recurrence = None
        method = create_method(create_braintree_buyer()[1])

        form, errors = self.process({
            'amount': '10.00',
            'paymethod': method.get_uri(),
            'product_id': seller_product.public_id
        })
        assert not errors, errors.as_text()
        assert 'payment_method_nonce' not in form.braintree_data
        eq_(form.braintree_data['payment_method_token'], method.provider_id)

    def test_recurring(self):
        seller, seller_product = create_seller()
        form, errors = self.process({
            'amount': '10.00',
            'nonce': 'nonce',
            'product_id': seller_product.public_id
        })
        eq_(form.errors.as_data()['product_id'][0].code, 'invalid')

    def test_different_amount_for_fixed_price(self):
        seller, seller_product = create_seller()
        form, errors = self.process({
            'amount': '1.23',
            'nonce': 'nonce',
            'product_id': seller_product.public_id
        })
        eq_(errors.as_data()['amount'][0].code, 'invalid')

    def test_allow_variable_amounts_for_donations(self):
        seller, seller_product = create_seller(
            seller_product_data={'public_id': 'charity-donation'}
        )
        form, errors = self.process({
            'amount': '99.00',
            'nonce': 'nonce',
            'product_id': seller_product.public_id
        })
        assert not errors, errors.as_text()
