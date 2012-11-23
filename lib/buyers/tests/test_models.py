from aesfield.field import EncryptedField
from nose.tools import eq_

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
