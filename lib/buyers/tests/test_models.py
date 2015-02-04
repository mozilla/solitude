from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase

from aesfield.field import EncryptedField
from nose.tools import eq_

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


class TestLockout(TestCase):

    def setUp(self):
        self.uid = 'test:uid'
        self.buyer = Buyer.objects.create(uuid=self.uid)

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
                assert buyer.pin_was_locked_out
            else:
                assert not res
                assert not buyer.pin_locked_out

    def test_clear(self):
        self.buyer.pin_failues = 1
        self.buyer.pin_locked_out = datetime.now()
        self.buyer.clear_lockout()
        eq_(self.buyer.pin_failures, 0)
        eq_(self.buyer.pin_locked_out, None)

    def test_was_locked_out(self):
        self.buyer.pin_failures = settings.PIN_FAILURES
        self.buyer.save()
        self.buyer.incr_lockout()
        self.buyer = self.buyer.reget()
        assert self.buyer.pin_was_locked_out
        self.buyer.clear_lockout()
        self.buyer = self.buyer.reget()
        assert self.buyer.pin_was_locked_out

    def test_clear_was_locked_out(self):
        self.buyer.pin_failures = settings.PIN_FAILURES
        self.buyer.save()
        self.buyer.incr_lockout()
        self.buyer = self.buyer.reget()
        assert self.buyer.pin_was_locked_out
        self.buyer.clear_lockout(clear_was_locked=True)
        self.buyer = self.buyer.reget()
        assert not self.buyer.pin_was_locked_out

    def test_under_timeout(self):
        self.buyer.pin_locked_out = (
            datetime.now() -
            timedelta(seconds=settings.PIN_FAILURE_LENGTH - 60))
        self.buyer.save()
        assert self.buyer.locked_out

    def test_over_timeout(self):
        self.buyer.pin_locked_out = (
            datetime.now() -
            timedelta(seconds=settings.PIN_FAILURE_LENGTH + 60))
        self.buyer.save()
        assert not self.buyer.locked_out
        eq_(self.buyer.reget().pin_locked_out, None)
