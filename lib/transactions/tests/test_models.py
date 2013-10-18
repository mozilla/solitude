from mock import ANY, patch
from nose.tools import eq_, ok_

from django.core.exceptions import ValidationError

from lib.sellers.models import Seller, SellerPaypal, SellerProduct
from lib.transactions import constants
from lib.transactions.models import Transaction
from solitude.base import APITest


class TestModel(APITest):

    def setUp(self):
        self.uuid = 'sample:uid'
        self.seller = Seller.objects.create(uuid=self.uuid)
        self.product = SellerProduct.objects.create(seller=self.seller,
                                                    external_id='xyz')

    def get_data(self, uid=None):
        return {
            'amount': 1,
            'provider': constants.PROVIDER_BANGO,
            'seller_product': self.product,
            'uuid': uid or self.uuid,
            'uid_pay': uid or self.uuid,
        }

    def test_uid_pay(self):
        data = self.get_data()
        data['uid_pay'] = 'abc'
        Transaction.create(**data)
        eq_(Transaction.objects.count(), 1)
        data['uuid'] = data['uuid'] + ':foo'

        with self.assertRaises(ValidationError):
            Transaction.create(**data)  # Uid pay conflicts.

        data['provider'] = constants.PROVIDER_PAYPAL
        Transaction.create(**data)
        eq_(Transaction.objects.count(), 2)

    def test_uid_support_optional(self):
        data = self.get_data()
        data['uid_pay'] = 'some:uid'
        Transaction.objects.create(**data)

        # uid_support still blank for the same provider.
        data['uuid'] = data['uuid'] + ':foo'
        data['uid_pay'] = data['uid_pay'] + 'some:uid'
        Transaction.objects.create(**data)

    def add_related(self):
        original = Transaction.create(**self.get_data())
        related = Transaction.create(related=original,
                                     **self.get_data(uid='foo'))
        return original, related

    def test_refunded(self):
        original, related = self.add_related()
        related.status = constants.STATUS_COMPLETED
        related.type = constants.TYPE_REFUND
        related.save()
        assert not related.reget().is_refunded()
        assert original.reget().is_refunded()

    def test_not_completed(self):
        original, related = self.add_related()
        related.type = constants.TYPE_REFUND
        related.save()
        assert not original.reget().is_refunded()

    def test_not_reversal(self):
        original, related = self.add_related()
        assert not original.reget().is_refunded()

    @patch('lib.transactions.models.statsd')
    def test_timed(self, statsd):
        trans = Transaction(**self.get_data())
        trans.save()
        ok_(not statsd.timing.called)

        trans.status = constants.STATUS_COMPLETED
        trans.save()
        statsd.timing.assert_called_with('transaction.status.completed', ANY)


class TestTransaction(APITest):

    def setUp(self):
        self.api_name = 'paypal'
        self.uuid = 'sample:uid'
        self.pay_url = self.get_list_url('pay')
        self.check_url = self.get_list_url('pay-check')
        self.seller = Seller.objects.create(uuid=self.uuid)
        self.product = SellerProduct.objects.create(seller=self.seller)
        SellerPaypal.objects.create(seller=self.seller,
                                    paypal_id='foo@bar.com')

    def get_data(self):
        return {'amount': '5',
                'currency': 'USD',
                'return_url': 'http://foo.com/return.url',
                'ipn_url': 'http://foo.com/ipn.url',
                'cancel_url': 'http://foo.com/cancel.url',
                'memo': 'Some memo',
                'seller_product': self.uuid}

    @patch('lib.paypal.client.Client.get_pay_key')
    def test_pay(self, key):
        key.return_value = {'pay_key': 'foo', 'status': 'CREATED',
                            'correlation_id': '123', 'uuid': '456'}
        res = self.client.post(self.pay_url, data=self.get_data())
        eq_(res.status_code, 201, res.content)
        qs = Transaction.objects.all()
        eq_(qs.count(), 1)

        obj = qs[0]
        eq_(obj.amount, 5)
        eq_(obj.uid_support, '123')
        eq_(obj.uuid, '456')
        eq_(obj.seller_product, self.product)
        eq_(obj.status, constants.STATUS_PENDING)

    @patch('lib.paypal.client.Client.get_pay_key')
    def test_pay_source(self, key):
        key.return_value = {'pay_key': 'foo', 'status': 'CREATED',
                            'correlation_id': '123', 'uuid': '456'}
        data = self.get_data()
        data['source'] = 'in-app'
        res = self.client.post(self.pay_url, data=data)
        eq_(res.status_code, 201)
        eq_(Transaction.objects.all()[0].source, 'in-app')

    @patch('lib.paypal.client.Client.check_purchase')
    def test_checked(self, check):
        check.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        pp = Transaction.create(uid_pay='foo', amount=5, uuid=self.uuid,
                                provider=constants.PROVIDER_PAYPAL,
                                seller_product=self.product)
        res = self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(res.status_code, 201)
        eq_(Transaction.objects.get(pk=pp.pk).status,
            constants.STATUS_CHECKED)

    @patch('lib.paypal.client.Client.check_purchase')
    def test_complete(self, check):
        check.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        pp = Transaction.create(uid_pay='foo', amount=5, uuid=self.uuid,
                                provider=constants.PROVIDER_PAYPAL,
                                seller_product=self.product)
        self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(Transaction.objects.get(pk=pp.pk).status,
            constants.STATUS_CHECKED)

        pp.status = constants.STATUS_COMPLETED
        pp.save()
        self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(Transaction.objects.get(pk=pp.pk).status,
            constants.STATUS_COMPLETED)

    @patch('lib.paypal.client.Client.check_purchase')
    def test_complete_not_there(self, check):
        check.return_value = {'status': 'COMPLETED', 'pay_key': 'foo'}
        Transaction.create(uid_pay='bar', amount=5, uuid=self.uuid,
                           provider=constants.PROVIDER_PAYPAL,
                           seller_product=self.product)
        res = self.client.post(self.check_url, data={'pay_key': 'foo'})
        eq_(res.status_code, 404)
