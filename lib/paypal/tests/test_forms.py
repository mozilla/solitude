from nose.tools import eq_
import test_utils

from lib.buyers.models import Buyer, BuyerPaypal
from lib.paypal.forms import AccountCheck, GetPersonal, PayValidation
from lib.sellers.models import Seller, SellerPaypal
from lib.transactions.models import Transaction


class TestValidation(test_utils.TestCase):

    def setUp(self):
        self.uuid = 'sample:uid'
        self.seller = Seller.objects.create(uuid=self.uuid)
        self.paypal = SellerPaypal.objects.create(seller=self.seller,
                                                  paypal_id='foo@bar.com')

    def get_data(self):
        return {'amount': '5',
                'currency': 'USD',
                'return_url': 'http://foo.com/return.url',
                'ipn_url': 'http://foo.com/return.url',
                'cancel_url': 'http://foo.com/cancel.url',
                'memo': 'Some memo',
                'use_preapproval': True,
                'seller': self.uuid}

    def test_seller(self):
        form = PayValidation(self.get_data())
        assert form.is_valid()
        eq_(form.cleaned_data['seller_email'], 'foo@bar.com')

    def test_no_paypal(self):
        self.paypal.delete()
        assert not PayValidation(self.get_data()).is_valid()

    def test_empty_paypal(self):
        self.paypal.paypal_id = ''
        self.paypal.save()
        assert not PayValidation(self.get_data()).is_valid()

    def test_no_seller(self):
        data = self.get_data()
        data['seller'] = 'foo'
        assert not PayValidation(data).is_valid()

    def test_buyer(self):
        buyer = Buyer.objects.create(uuid='sample:uid')
        data = self.get_data()
        data['buyer'] = buyer.uuid
        form = PayValidation(data)
        assert form.is_valid(), form.errors
        eq_(form.cleaned_data['preapproval'], '')

    def test_buyer_optional(self):
        data = self.get_data()
        data['buyer'] = 'not:there:uid'
        form = PayValidation(data)
        assert form.is_valid(), form.errors
        eq_(form.cleaned_data['preapproval'], '')

    def test_buyer_preapproval(self):
        buyer = Buyer.objects.create(uuid='sample:uid')
        BuyerPaypal.objects.create(buyer=buyer, key='foo')
        data = self.get_data()
        data['buyer'] = buyer.uuid
        form = PayValidation(data)
        assert form.is_valid(), form.errors
        eq_(form.cleaned_data['preapproval'], 'foo')

    def test_buyer_preapproval_ignored(self):
        buyer = Buyer.objects.create(uuid='sample:uid')
        BuyerPaypal.objects.create(buyer=buyer, key='foo')
        data = self.get_data()
        data['use_preapproval'] = False
        data['buyer'] = buyer.uuid
        form = PayValidation(data)
        assert form.is_valid(), form.errors
        eq_(form.cleaned_data['preapproval'], '')

    def test_currency(self):
        form = PayValidation(self.get_data())
        assert form.is_valid()
        eq_(form.cleaned_data['currency'], 'USD')

    def test_duplicate_uuid(self):
        Transaction.objects.create(seller=self.paypal, amount=5,
                                   uuid='sample:uuid')
        data = self.get_data()
        data['uuid'] = 'sample:uuid'
        form = PayValidation(data)
        assert not form.is_valid(), form.errors


class TestKeyValidation(test_utils.TestCase):

    def setUp(self):
        self.uuid = 'sample:uid'
        self.seller = Seller.objects.create(uuid=self.uuid)
        self.paypal = SellerPaypal.objects.create(seller=self.seller,
                                                  paypal_id='foo@bar.com')

    def test_empty_token(self):
        form = GetPersonal({'seller': self.uuid})
        assert not form.is_valid()

    def test_no_seller(self):
        form = GetPersonal()
        assert not form.is_valid()

    def test_token(self):
        self.paypal.token = 'token'
        self.paypal.secret = 'secret'
        self.paypal.save()

        form = GetPersonal({'seller': self.uuid})
        assert form.is_valid()


class TestValidation(test_utils.TestCase):

    def setUp(self):
        self.uuid = 'sample:uid'
        self.seller = Seller.objects.create(uuid=self.uuid)
        self.paypal = SellerPaypal.objects.create(seller=self.seller)

    def test_empty_token(self):
        form = AccountCheck({'seller': self.uuid})
        assert not form.is_valid()

    def test_no_seller(self):
        form = AccountCheck()
        assert not form.is_valid()

    def test_empty_paypal_id(self):
        self.paypal.token = 'token'
        self.paypal.save()

        form = AccountCheck({'seller': self.uuid})
        assert not form.is_valid()

    def test_good(self):
        self.paypal.paypal_id = 'asd'
        self.paypal.token = 'token'
        self.paypal.save()

        form = AccountCheck({'seller': self.uuid})
        assert form.is_valid()
        eq_(form.cleaned_data['paypal_id'], 'asd')
        eq_(form.cleaned_data['token'], 'token')
