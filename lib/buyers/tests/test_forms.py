from django.test import TestCase

from lib.buyers.constants import PIN_4_NUMBERS_LONG, PIN_ONLY_NUMBERS
from lib.buyers.forms import PinForm
from lib.buyers.models import Buyer


class BuyerFormTest(TestCase):

    def setUp(self):
        self.data = {'uuid': 'a:uuid'}
        Buyer.objects.create(uuid='a:uuid')

    def test_good_pin(self):
        self.data['pin'] = '1234'
        form = PinForm(self.data)
        assert form.is_valid()

    def test_too_long_pin(self):
        self.data['pin'] = '12345'
        form = PinForm(self.data)
        assert not form.is_valid()
        assert PIN_4_NUMBERS_LONG in form.errors['pin']

    def test_too_short_pin(self):
        self.data['pin'] = '123'
        form = PinForm(self.data)
        assert not form.is_valid()
        assert PIN_4_NUMBERS_LONG in form.errors['pin']

    def test_partially_numeric_pin(self):
        self.data['pin'] = '123a'
        form = PinForm(self.data)
        assert not form.is_valid()
        assert PIN_ONLY_NUMBERS in form.errors['pin']

    def test_completely_alpha_pin(self):
        self.data['pin'] = 'asfa'
        form = PinForm(self.data)
        assert not form.is_valid()
        assert PIN_ONLY_NUMBERS in form.errors['pin']
