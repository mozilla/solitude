from datetime import datetime

from aesfield.field import EncryptedField
from nose.tools import eq_

from django.conf import settings
from django.test import TestCase

from lib.buyers.models import Buyer, BuyerPaypal


class TestEncryption(TestCase):
    # This is mostly because of a lack of tests in aesfield.
    # Let's just check this all works as we'd expect.

    def setUp(self):
        self.uid = 'test:uid'
        self.buyer = Buyer.objects.create(uuid=self.uid)

    def test_add_empty(self):
        bp = BuyerPaypal.objects.create(buyer=self.buyer)
        eq_(bp.key, None)

    def test_add_something(self):
        bp = BuyerPaypal.objects.create(buyer=self.buyer, key='foo')
        eq_(BuyerPaypal.objects.get(pk=bp.pk).key, 'foo')

    def test_update_something(self):
        bp = BuyerPaypal.objects.create(buyer=self.buyer, key='foo')
        bp.key = 'foopy'
        bp.save()
        eq_(BuyerPaypal.objects.get(pk=bp.pk).key, 'foopy')

    def test_set_empty(self):
        bp = BuyerPaypal.objects.create(buyer=self.buyer, key='foo')
        bp.key = ''
        bp.save()
        eq_(BuyerPaypal.objects.get(pk=bp.pk).key, '')

    def test_filter(self):
        with self.assertRaises(EncryptedField):
            BuyerPaypal.objects.filter(key='bar')

    def test_locked_out(self):
        assert not self.buyer.locked_out
        self.buyer.pin_locked_out = datetime.now()
        self.buyer.save()
        assert self.buyer.reget().locked_out

    def test_increment(self):
        for x in range(1, settings.PIN_FAILURES + 1):
            res = self.buyer.incr_lockout()
            buyer = self.buyer.reget()
            eq_(buyer.pin_failures, x)

            # On the last pass, we should be locked out.
            if x == settings.PIN_FAILURES:
                assert res
                assert buyer.pin_locked_out
            else:
                assert not res
                assert not buyer.pin_locked_out

    def test_clear(self):
        self.buyer.pin_failues = 1
        self.buyer.pin_locked_out = datetime.now()
        self.buyer.clear_lockout()
        eq_(self.buyer.pin_failures, 0)
        eq_(self.buyer.pin_locked_out, None)
