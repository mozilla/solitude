from django.core.exceptions import ValidationError

from mock import ANY, patch
from nose.tools import eq_, ok_

from lib.sellers.models import Seller, SellerProduct
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

        data['provider'] = constants.PROVIDER_REFERENCE
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

    def test_no_provider(self):
        data = self.get_data()
        del data['provider']
        Transaction.objects.create(**data)

    def test_short_id(self):
        obj = Transaction.objects.create(**self.get_data())
        ok_(obj.create_short_uid().startswith('ba-'))

    def test_short_id_no_provider(self):
        data = self.get_data()
        del data['provider']
        obj = Transaction.objects.create(**data)
        ok_(obj.create_short_uid().startswith('dk-'))
