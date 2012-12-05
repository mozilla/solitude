from django.test import TestCase

from lib.buyers.forms import BuyerForm


class BuyerFormTest(TestCase):

    def setUp(self):
        self.data = {'uuid': 'a:uuid'}

    def test_good_pin(self):
        self.data['pin'] = '1234'
        form = BuyerForm(self.data)
        assert form.is_valid()

    def test_too_long_pin(self):
        self.data['pin'] = '12345'
        form = BuyerForm(self.data)
        assert not form.is_valid()
        assert 'PIN must be exactly 4 numbers long' in form.errors['pin']

    def test_too_short_pin(self):
        self.data['pin'] = '123'
        form = BuyerForm(self.data)
        assert not form.is_valid()
        assert 'PIN must be exactly 4 numbers long' in form.errors['pin']

    def test_partially_numeric_pin(self):
        self.data['pin'] = '123a'
        form = BuyerForm(self.data)
        assert not form.is_valid()
        assert 'PIN may only consists of numbers' in form.errors['pin']

    def test_completely_alpha_pin(self):
        self.data['pin'] = 'asfa'
        form = BuyerForm(self.data)
        assert not form.is_valid()
        assert 'PIN may only consists of numbers' in form.errors['pin']
