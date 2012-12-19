import json
from unittest import TestCase

import mock
from nose.tools import eq_, ok_

from ..forms import (CreateBankDetailsForm,
                     CreateBillingConfigurationForm as BillingForm,
                     PriceForm)
from .samples import good_bank_details, good_billing_request


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


@mock.patch('lib.bango.forms.URLField.clean')
class TestBilling(TestCase):

    def setUp(self):
        self.billing = good_billing_request.copy()
        self.billing['seller_product_bango'] = '/blah/'

    def test_form(self, clean):
        ok_(PriceForm({'amount': 1, 'currency': 'NZD'}))

    def test_billing(self, clean):
        ok_(BillingForm(self.billing).is_valid())

    def test_no_json(self, clean):
        del self.billing['prices']
        assert not BillingForm(self.billing).is_valid()

    def test_bad_json(self, clean):
        self.billing['prices'] = 'blargh'
        assert not BillingForm(self.billing).is_valid()

        self.billing['prices'] = json.dumps(['foo'])
        assert not BillingForm(self.billing).is_valid()

    def test_no_prices(self, clean):
        self.billing['prices'] = []
        form = BillingForm(self.billing)
        form.is_valid()
        eq_(form.errors['prices'], ['This field is required.'])

    def test_price_error(self, clean):
        self.billing['prices'] = [{'amount': 1, 'currency': 'FOO'}]
        form = BillingForm(self.billing)
        form.is_valid()
        ok_('Select a valid choice' in form.errors['prices'][0])

    def test_iterate(self, clean):
        form = BillingForm(self.billing)
        form.is_valid()
        for price in form.cleaned_data['prices']:
            ok_(price.is_valid())
