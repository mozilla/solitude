# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse

from mock import Mock, patch
from nose.tools import eq_, ok_

import samples
import utils
from ..constants import CANCEL, OK
from lib.sellers.models import Seller, SellerProduct
from lib.transactions import constants
from lib.transactions.constants import STATUS_COMPLETED
from lib.transactions.models import Transaction
from solitude.base import APITest
from ..utils import sign


class TestNotification(APITest):

    def setUp(self):
        self.trans_uuid = 'some-transaction-uid'
        sellers = utils.make_sellers(uuid='seller-uuid')
        self.seller = sellers.seller
        self.product = sellers.product
        self.token = '<bango-guid>'
        self.response_code = OK
        self.response_msg = 'Success'
        self.bango_trans_id = '56789'
        self.trans = Transaction.objects.create(
            amount=1, provider=constants.PROVIDER_BANGO,
            seller_product=self.product,
            uuid=self.trans_uuid,
            uid_pay='external-trans-uid'
        )
        self.url = reverse('bango:notification')
        self.sig = sign(self.trans_uuid)
        p = patch('lib.bango.forms.get_client')
        self.addCleanup(p.stop)
        self.get_client = p.start()

    def setup_token(self, Signature=None, MerchantTransactionId=None,
                    ResponseMessage=None, ResponseCode=None,
                    BangoTransactionId=None, res=None):
        # This is the mock CheckToken result.
        if not res:
            res = Mock()
            res.Signature = Signature or self.sig
            res.MerchantTransactionId = (MerchantTransactionId or
                                         self.trans_uuid)
            res.ResponseCode = ResponseCode or self.response_code
            res.ResponseMessage = ResponseMessage or self.response_msg
            res.BangoTransactionId = BangoTransactionId or self.bango_trans_id

        # Take a deep breath before you read this.
        # We are mocking: get_client().client().service.CheckToken(token=...)

        get_client = Mock()

        client = Mock()
        client.service.CheckToken.return_value = res

        get_client.client.return_value = client
        self.get_client.return_value = get_client

    def data(self, overrides=None):
        data = {'moz_transaction': self.trans_uuid,
                'moz_signature': self.sig,
                'billing_config_id': '1234',
                'bango_trans_id': self.bango_trans_id,
                'bango_response_code': self.response_code,
                'amount': '0.99',
                'currency': 'EUR',
                'bango_token': self.token,
                'bango_response_message': self.response_msg}
        if overrides:
            data.update(overrides)
        return data

    def post(self, data, expected_status=204):
        res = self.client.post(self.url, data=data)
        eq_(res.status_code, expected_status, (res.status_code, res.content))

    @patch('lib.bango.views.notification.log_cef')
    def test_success(self, log_cef):
        self.setup_token()
        data = self.data()
        self.post(data)
        tr = self.trans.reget()
        eq_(tr.status, constants.STATUS_COMPLETED)
        eq_(tr.amount, Decimal(data['amount']))
        eq_(tr.currency, data['currency'])
        ok_(tr.uid_support)
        assert log_cef.called
        ok_(not tr.carrier)

    def test_no_price(self):
        self.setup_token()
        data = self.data()
        del data['amount']
        del data['currency']
        self.post(data)
        tr = self.trans.reget()
        eq_(tr.amount, None)
        eq_(tr.currency, '')

    def test_empty_price(self):
        self.setup_token()
        data = self.data()
        data['amount'] = ''
        data['currency'] = ''
        self.post(data)
        tr = self.trans.reget()
        eq_(tr.amount, None)
        eq_(tr.currency, '')

    def test_failed(self):
        self.response_code = 'NOT OK'
        self.setup_token()
        self.post(self.data())
        tr = self.trans.reget()
        eq_(tr.status, constants.STATUS_FAILED)

    def test_cancelled(self):
        self.response_code = CANCEL
        self.setup_token()
        self.post(self.data())
        tr = self.trans.reget()
        eq_(tr.status, constants.STATUS_CANCELLED)

    def test_incorrect_sig(self):
        self.sig = sign(self.trans_uuid) + 'garbage'
        self.setup_token()
        data = self.data()
        self.post(data, expected_status=400)

    def test_missing_sig(self):
        self.setup_token()
        data = self.data()
        del data['moz_signature']
        self.post(data, expected_status=400)

    def test_missing_transaction(self):
        self.setup_token()
        data = self.data()
        del data['moz_transaction']
        self.post(data, expected_status=400)

    def test_unknown_transaction(self):
        self.setup_token()
        self.post(self.data({'moz_transaction': 'does-not-exist'}),
                  expected_status=400)

    def test_long_int_transaction(self):
        # The token check service returns non-string fields, bah!
        self.setup_token(BangoTransactionId=long(self.bango_trans_id))
        self.post(self.data())

    def test_already_completed(self):
        self.setup_token()
        self.trans.status = constants.STATUS_COMPLETED
        self.trans.save()
        self.post(self.data(), expected_status=400)

    def test_expired_transaction(self):
        self.setup_token()
        self.trans.created = datetime.now() - timedelta(seconds=62)
        self.trans.save()
        with self.settings(TRANSACTION_EXPIRY=60):
            self.post(self.data(), expected_status=400)

    @patch('lib.bango.forms.log_cef')
    def test_tampered_response_code(self, log_cef):
        self.setup_token(ResponseCode='tampered-with')
        self.post(self.data(), expected_status=400)
        assert log_cef.called

    def test_tampered_response_msg(self):
        self.setup_token(ResponseMessage='tampered-with')
        self.post(self.data(), expected_status=400)

    def test_tampered_bango_trans(self):
        self.setup_token(BangoTransactionId='tampered-with')
        self.post(self.data(), expected_status=400)

    def test_tampered_moz_trans(self):
        self.setup_token(MerchantTransactionId='tampered-with')
        self.post(self.data(), expected_status=400)

    def test_tampered_sig(self):
        self.setup_token(Signature='tampered-with')
        self.post(self.data(), expected_status=400)

    def test_unknown_token(self):
        # When unknown, all fields are set to None.
        res = Mock()
        res.Signature = None
        res.MerchantTransactionId = None
        res.ResponseCode = None
        res.ResponseMessage = None
        self.setup_token(res=res)

        self.post(self.data(), expected_status=400)

    def test_network(self):
        self.setup_token()
        data = self.data()
        data['network'] = 'CAN_TELUS'
        self.post(data)
        tr = self.trans.reget()
        eq_(tr.region, 'CAN')
        eq_(tr.carrier, 'TELUS')


@patch.object(settings, 'BANGO_BASIC_AUTH', {'USER': 'f', 'PASSWORD': 'b'})
class TestEvent(APITest):

    def setUp(self):
        self.trans_uuid = 'external-trans-uid'
        self.seller = Seller.objects.create(uuid='seller-uuid')
        self.product = SellerProduct.objects.create(seller=self.seller,
                                                    external_id='xyz')
        self.trans = Transaction.objects.create(
            amount=1, provider=constants.PROVIDER_BANGO,
            seller_product=self.product,
            uuid=self.trans_uuid,
            uid_pay='bango-trans-uid'
        )
        self.url = reverse('bango:event')

    def post(self, data=None, notice=samples.event_notification,
             expected=204):
        if data is None:
            data = {
                'notification': notice,
                'password': 'b',
                'username': 'f'
            }
        res = self.client.post(self.url, data=data)
        eq_(res.status_code, expected, (res.status_code, res.content))

    def test_missing(self):
        self.post(data={}, expected=400)

    @patch('lib.bango.views.event.log_cef')
    def test_good(self, log_cef):
        self.post()
        trans = self.trans.reget()
        eq_(trans.status, STATUS_COMPLETED)
        assert log_cef.called

    def test_no_action(self):
        self.post(notice=samples.event_notification_no_action,
                  expected=400)

    def test_no_data(self):
        self.post(notice=samples.event_notification_no_data,
                  expected=400)

    def test_no_trans(self):
        self.post(notice=samples.event_notification_cp_trans_id,
                  expected=400)

    def test_not_changed(self):
        self.trans.status = STATUS_COMPLETED
        self.trans.save()
        self.post()
        trans = self.trans.reget()
        eq_(trans.status, STATUS_COMPLETED)

    def test_wrong_auth(self):
        data = {'notification': samples.event_notification,
                'password': 'nope',
                'username': 'yes'}
        self.post(data, expected=400)
