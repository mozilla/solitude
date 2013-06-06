# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings

from mock import patch
from nose.tools import eq_, ok_

from lib.sellers.models import Seller, SellerProduct
from lib.transactions import constants
from lib.transactions.constants import STATUS_COMPLETED
from lib.transactions.models import Transaction
from solitude.base import APITest

from ..constants import CANCEL
from ..utils import sign

import samples


class TestNotification(APITest):
    api_name = 'bango'

    def setUp(self):
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
        self.url = self.get_list_url('notification')

    def data(self, overrides=None):
        data = {'moz_transaction': self.trans_uuid,
                'moz_signature': sign(self.trans_uuid),
                'billing_config_id': '1234',
                'bango_trans_id': '56789',
                'bango_response_code': 'OK',
                'amount': '0.99',
                'currency': 'EUR',
                'bango_response_message': 'Success'}
        if overrides:
            data.update(overrides)
        return data

    def post(self, data, expected_status=201):
        res = self.client.post(self.url, data=data)
        eq_(res.status_code, expected_status, res.content)
        return json.loads(res.content)

    def test_success(self):
        data = self.data()
        self.post(data)
        tr = self.trans.reget()
        eq_(tr.status, constants.STATUS_COMPLETED)
        eq_(tr.amount, Decimal(data['amount']))
        eq_(tr.currency, data['currency'])
        ok_(tr.uid_support)

    def test_no_price(self):
        data = self.data()
        del data['amount']
        del data['currency']
        self.post(data)
        tr = self.trans.reget()
        eq_(tr.amount, None)
        eq_(tr.currency, '')

    def test_empty_price(self):
        data = self.data()
        data['amount'] = ''
        data['currency'] = ''
        self.post(data)
        tr = self.trans.reget()
        eq_(tr.amount, None)
        eq_(tr.currency, '')

    def test_failed(self):
        self.post(self.data(overrides={'bango_response_code': 'NOT OK'}))
        tr = self.trans.reget()
        eq_(tr.status, constants.STATUS_FAILED)

    def test_cancelled(self):
        self.post(self.data(overrides={'bango_response_code':
                                       CANCEL}))
        tr = self.trans.reget()
        eq_(tr.status, constants.STATUS_CANCELLED)

    def test_incorrect_sig(self):
        data = self.data({'moz_signature': sign(self.trans_uuid) + 'garbage'})
        self.post(data, expected_status=400)

    def test_missing_sig(self):
        data = self.data()
        del data['moz_signature']
        self.post(data, expected_status=400)

    def test_missing_transaction(self):
        data = self.data()
        del data['moz_transaction']
        self.post(data, expected_status=400)

    def test_unknown_transaction(self):
        self.post(self.data({'moz_transaction': 'does-not-exist'}),
                  expected_status=400)

    def test_already_completed(self):
        self.trans.status = constants.STATUS_COMPLETED
        self.trans.save()
        self.post(self.data(), expected_status=400)

    def test_expired_transaction(self):
        self.trans.created = datetime.now() - timedelta(seconds=62)
        self.trans.save()
        with self.settings(TRANSACTION_EXPIRY=60):
            self.post(self.data(), expected_status=400)


@patch.object(settings, 'BANGO_BASIC_AUTH', {'USER': 'f', 'PASSWORD': 'b'})
class TestEvent(APITest):
    api_name = 'bango'

    def setUp(self):
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
        self.url = self.get_list_url('event')

    def post(self, data=None, expected=201):
        if data is None:
            data = {
                'notification': samples.event_notification,
                'password': 'b',
                'username': 'f'
            }
        res = self.client.post(self.url, data=data)
        eq_(res.status_code, expected)
        return json.loads(res.content)

    def test_missing(self):
        self.post(data={}, expected=400)

    def test_good(self):
        self.post()
        trans = self.trans.reget()
        eq_(trans.status, STATUS_COMPLETED)

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
