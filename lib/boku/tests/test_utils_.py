from decimal import Decimal

from django.test import TestCase

from nose.tools import eq_, ok_, raises

from lib.boku.errors import VerificationError
from lib.boku.tests.utils import EventTest
from lib.boku.utils import fix_price, verify


class TestFixPrice(TestCase):

    def test_mxn(self):
        eq_(fix_price(Decimal('100'), 'MXN'), Decimal('1.00'))

    @raises(KeyError)
    def test_bad_currency_name_raises_keyerror(self):
        eq_(fix_price(Decimal('100'), 'FOO'))

    @raises(AssertionError)
    def test_decimal_required_for_value(self):
        eq_(fix_price(100.0, 'MXN'))


class TestVerify(EventTest):

    def test_good(self):
        self.add_seller_boku()
        verify(self.trans, Decimal('1.00'), 'MXN')

    @raises(VerificationError)
    def test_wrong_amount(self):
        self.add_seller_boku()
        ok_(verify(self.trans.uid_support, Decimal('1.01'), 'MXN'))

    @raises(VerificationError)
    def test_wrong_currency(self):
        self.add_seller_boku()
        ok_(verify(self.trans.uid_support, Decimal('1.01'), 'FOO'))
