from unittest import TestCase

import mock
from ..forms import CreateBankDetailsForm
from .samples import good_bank_details


@mock.patch('lib.bango.forms.URLField.clean')
class TestBankDetails(TestCase):

    def setUp(self):
        self.bank = good_bank_details.copy()
        self.bank['seller_product'] = '/generic/seller/1/'

    def test_valid(self, clean):
        assert CreateBankDetailsForm(self.bank).is_valid()

    def test_missing(self, clean):
        del self.bank['bankAccountNumber']
        assert not CreateBankDetailsForm(self.bank).is_valid()

    def test_iban(self, clean):
        del self.bank['bankAccountNumber']
        self.bank['bankAccountIban'] = 'foo'
        assert CreateBankDetailsForm(self.bank).is_valid()
