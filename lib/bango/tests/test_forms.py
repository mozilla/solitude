import json

from django.conf import settings

import mock
from nose.tools import eq_, ok_

from ..forms import (CreateBankDetailsForm, CreateBillingConfigurationForm,
                     CreateBillingConfigurationForm as BillingForm, EventForm,
                     PackageForm, PriceForm, VatNumberForm)
from .samples import (event_notification, good_address, good_bank_details,
                      good_billing_request)
from lib.sellers.models import Seller, SellerProduct
from lib.transactions import constants
from lib.transactions.models import Transaction
from solitude.base import APITest

import samples


@mock.patch('lib.bango.forms.URLField.clean')
class TestBankDetails(APITest):

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
class TestBilling(APITest):

    def setUp(self):
        self.billing = good_billing_request.copy()
        self.billing['transaction_uuid'] = 'foo'
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


@mock.patch('lib.bango.forms.URLField.clean')
class TestPackage(APITest):

    def test_no_auth(self, clean):
        form = PackageForm(good_address)
        ok_(form.is_valid())
        ok_(not 'eventNotificationURL' in form.bango_data)

    def test_auth(self, clean):
        with self.settings(BANGO_NOTIFICATION_URL='http://f.com',
                           BANGO_BASIC_AUTH={'USER': 'u', 'PASSWORD': 'p'}):
            form = PackageForm(good_address)
            ok_(form.is_valid())
            eq_(form.bango_data['eventNotificationURL'], 'http://f.com')

    def compute_application_size(self, data, submitted_size, computed_size):
        data['application_size'] = submitted_size
        form = CreateBillingConfigurationForm(data)
        ok_(form.is_valid())
        eq_(form.bango_data['application_size'], computed_size)

    def test_submit_bango_number_with_application_size(self, clean):
        data = samples.good_billing_request
        data['transaction_uuid'] = 'foo'
        self.compute_application_size(data, None, 1)
        self.compute_application_size(data, 300, 1)
        self.compute_application_size(data, 388096, 379)


class TestVat(APITest):

    def test_delete(self):
        form = VatNumberForm({})
        ok_(form.is_valid())
        eq_(form.bango_data, {})
        eq_(form.bango_meta['method'], 'DeleteVATNumber')

    def test_change(self):
        form = VatNumberForm({'vatNumber': '123'})
        ok_(form.is_valid())
        eq_(form.bango_data, {'vatNumber': '123'})
        eq_(form.bango_meta['method'], 'SetVATNumber')


@mock.patch.object(settings, 'BANGO_BASIC_AUTH',
                   {'USER': 'f', 'PASSWORD': 'b'})
class TestEvent(APITest):

    def test_empty(self):
        form = EventForm()
        ok_(not form.is_valid())

    def test_gunk(self):
        form = EventForm({'notification': 'fooo!'})
        ok_(not form.is_valid())

    def test_wrong_action(self):
        sample = event_notification.replace('PAYMENT', 'NOT')
        form = EventForm({'notification': sample})
        ok_(not form.is_valid())

    def test_no_action(self):
        sample = event_notification.replace('OK', 'NOT OK')
        form = EventForm({'notification': sample})
        ok_(not form.is_valid())

    def test_no_transaction(self):
        form = EventForm({'notification': event_notification})
        ok_(not form.is_valid())

    def create(self):
        # TODO this isn't great.
        self.trans_uuid = 'some-transaction-uid'
        self.seller = Seller.objects.create(uuid='seller-uuid')
        self.product = SellerProduct.objects.create(seller=self.seller,
                                                    external_id='xyz')
        self.trans = Transaction.objects.create(
            amount=1, provider=constants.SOURCE_BANGO,
            seller_product=self.product,
            uuid=self.trans_uuid,
            uid_pay='external-trans-uid'
        )

    def test_check_good(self):
        self.create()
        form = EventForm({'notification': event_notification,
                          'username': 'f', 'password': 'b'})
        ok_(form.is_valid(), form.errors)

    def test_check_wrong(self):
        self.create()
        form = EventForm({'notification': event_notification,
                          'username': 'f', 'password': 'x'})
        ok_(not form.is_valid())
        ok_('__all__' in form.errors)

    def test_wierd(self):
        self.create()
        self.trans.status = constants.STATUS_CANCELLED
        self.trans.save()
        form = EventForm({'notification': event_notification})
        ok_(not form.is_valid())
