from decimal import Decimal

from nose.tools import eq_
import test_utils

from lib.sellers.models import Seller, SellerPaypal, SellerProduct
from lib.transactions import constants
from lib.transactions.models import Transaction
from lib.transactions.utils import completed, refunded, reversal


class TestIPN(test_utils.TestCase):

    def setUp(self):
        self.transaction_uuid = 'transaction:uid'
        self.seller = Seller.objects.create(uuid='seller:uid')
        self.product = SellerProduct.objects.create(seller=self.seller)
        self.paypal = SellerPaypal.objects.create(seller=self.seller,
                                                 paypal_id='foo@bar.com')
        self.transaction = Transaction.objects.create(
            type=constants.TYPE_PAYMENT,
            status=constants.STATUS_PENDING,
            uid_support='asd',
            uid_pay='asd',
            seller_product=self.product,
            provider=constants.SOURCE_PAYPAL,
            amount=Decimal('10'),
            currency='USD',
            uuid=self.transaction_uuid)

    def get_transaction(self):
        return Transaction.objects.get(pk=self.transaction.pk)

    def test_complete(self):
        completed({'tracking_id': self.transaction_uuid}, {})
        eq_(self.get_transaction().status, constants.STATUS_COMPLETED)

    def test_complete_missing(self):
        eq_(completed({'tracking_id': self.transaction_uuid + 'nope'}, {}),
            False)

    def test_complete_already(self):
        self.transaction.status = constants.STATUS_COMPLETED
        self.transaction.save()
        eq_(completed({'tracking_id': self.transaction_uuid}, {}), False)

    def test_refund(self):
        self.transaction.status = constants.STATUS_COMPLETED
        self.transaction.save()
        refunded({'tracking_id': self.transaction_uuid, 'pay_key': 'foo'},
                 {'amount': {'amount': 10, 'currency': 'USD'}})
        types = [s.type for s in Transaction.objects.all()]
        eq_([constants.TYPE_REFUND, constants.TYPE_PAYMENT], types)

    def test_refund_amount(self):
        self.transaction.status = constants.STATUS_COMPLETED
        self.transaction.save()
        refunded({'tracking_id': self.transaction_uuid, 'pay_key': 'foo'},
                 {'amount': {'amount': 10, 'currency': 'USD'}})
        trans = Transaction.objects.get(type=constants.TYPE_REFUND)
        eq_(trans.amount, Decimal('-10'))
        eq_(trans.currency, 'USD')

    def test_refund_missing(self):
        eq_(refunded({'tracking_id': self.transaction_uuid + 'nope'}, {}),
            False)

    def test_refund_already_done(self):
        Transaction.objects.create(
            type=constants.TYPE_REFUND,
            status=constants.STATUS_PENDING,
            uid_support='asd-123',
            uid_pay='asd-123',
            seller_product=self.product,
            amount=Decimal('-10'),
            currency='USD',
            provider=constants.SOURCE_PAYPAL,
            uuid=self.transaction_uuid + 'another',
            related=self.transaction)

        eq_(refunded({'tracking_id': self.transaction_uuid}, {}), False)

    def test_reject_missing(self):
        eq_(reversal({'tracking_id': self.transaction_uuid + 'nope'}, {}),
            False)

    def test_rejected_already_done(self):
        Transaction.objects.create(
            type=constants.TYPE_REVERSAL,
            status=constants.STATUS_PENDING,
            uid_support='asd-123',
            uid_pay='asd-123',
            seller_product=self.product,
            amount=Decimal('-10'),
            currency='USD',
            provider=constants.SOURCE_PAYPAL,
            uuid=self.transaction_uuid + 'another',
            related=self.transaction)

        eq_(reversal({'tracking_id': self.transaction_uuid}, {}), False)

    def test_rejected(self):
        self.transaction.status = constants.STATUS_COMPLETED
        self.transaction.save()
        reversal({'tracking_id': self.transaction_uuid, 'pay_key': 'foo'},
                 {'amount': {'amount': 10, 'currency': 'USD'}})
        types = [s.type for s in Transaction.objects.all()]
        eq_([constants.TYPE_REVERSAL, constants.TYPE_PAYMENT], types)
