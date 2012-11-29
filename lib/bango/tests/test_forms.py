from unittest import TestCase

from django import forms

import mock
from nose.tools import raises

from lib.sellers.resources import SellerResource
from ..forms import CreateBankDetailsForm, URLField
from .samples import good_bank_details


class TestURLField(TestCase):

    def test_valid(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_nope(self):
        self.field = URLField(to='lib.sellers.resources.Nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_module(self):
        self.field = URLField(to='lib.nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(ValueError)
    def test_more_module(self):
        self.field = URLField(to='nope')
        assert isinstance(self.field.to_instance(), SellerResource)

    @raises(forms.ValidationError)
    def test_not_there(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        self.field.clean('/generic/seller/1/')

    @raises(forms.ValidationError)
    def test_not_found(self):
        self.field = URLField(to='lib.sellers.resources.SellerResource')
        self.field.clean('/blarg/blarg/1/')


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
