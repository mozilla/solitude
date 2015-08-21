from datetime import datetime
from decimal import Decimal

from django.core.urlresolvers import reverse

import mock
from braintree.successful_result import SuccessfulResult
from braintree.transaction import Transaction
from braintree.transaction_gateway import TransactionGateway
from nose.tools import eq_

from lib.brains.tests.base import (
    BraintreeTest, create_braintree_buyer, create_method, create_seller,
    ProductsTest)


def transaction(**kw):
    transaction = {
        'amount': '5.00',
        'card_type': 'visa',
        'created_at': datetime.now(),
        'id': 'test-id',
        'last_4': '7890',
        'tax_amount': '0.00',
        'token': 'da-token',
        'updated_at': datetime.now(),
        'currency_iso_code': 'USD',
    }
    transaction.update(**kw)
    return Transaction(None, transaction)


def successful_method(**kw):
    return SuccessfulResult({'transaction': transaction(**kw)})


class TestSale(BraintreeTest, ProductsTest):
    gateways = {'sale': TransactionGateway}

    def setUp(self):
        super(TestSale, self).setUp()
        self.url = reverse('braintree:sale')

    def test_allowed(self):
        self.allowed_verbs(self.url, ['post'])

    def test_ok(self):
        self.mocks['sale'].create.return_value = successful_method()
        self.product_mock.get('moz-brick').recurrence = None
        seller, seller_product = create_seller()

        res = self.client.post(
            self.url,
            data={
                'amount': 10,
                'nonce': 'some-nonce',
                'product_id': 'moz-brick'
            })

        self.mocks['sale'].create.assert_called_with({
            'amount': Decimal('10'),
            'type': 'sale',
            'options': {'submit_for_settlement': True},
            'payment_method_nonce': u'some-nonce'}
        )
        eq_(res.status_code, 200)
        generic = res.json['mozilla']['generic']
        eq_(generic['buyer'], None)
        eq_(generic['uid_support'], 'test-id')
        eq_(generic['seller'], seller.get_uri())
        eq_(generic['seller_product'], seller_product.get_uri())

    def test_failure(self):
        res = self.client.post(
            self.url,
            data={
                'amount': '5',
                'nonce': 'some-nonce',
                'product_id': 'moz-brick'}
        )
        eq_(res.status_code, 422)

    def test_pay_method(self):
        self.mocks['sale'].create.return_value = successful_method()
        self.product_mock.get('moz-brick').recurrence = None
        seller, seller_product = create_seller()
        method = create_method(create_braintree_buyer()[1])

        res = self.client.post(
            self.url,
            data={
                'amount': '10.00',
                'paymethod': method.get_uri(),
                'product_id': 'moz-brick'
            }
        )

        self.mocks['sale'].create.assert_called_with({
            'amount': Decimal('10.00'),
            'type': 'sale',
            'options': {'submit_for_settlement': True},
            'payment_method_token': mock.ANY}
        )
        eq_(res.status_code, 200)
        generic = res.json['mozilla']['generic']
        eq_(generic['buyer'], method.braintree_buyer.buyer.get_uri())
        braintree = res.json['mozilla']['braintree']
        eq_(braintree['paymethod'], method.get_uri())

    def test_multiple(self):
        self.mocks['sale'].create.return_value = successful_method()
        seller, seller_product = create_seller()

        data = {'amount': 5, 'nonce': 123, 'product_id': 'brick'}
        res = self.client.post(self.url, data=data)
        eq_(res.status_code, 200, res.content)

        self.mocks['sale'].create.return_value = successful_method(id='two-id')
        res = self.client.post(self.url, data=data)
        eq_(res.status_code, 200, res.content)
