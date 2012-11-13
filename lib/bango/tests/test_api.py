import json

import mock
from mock import Mock
from nose.tools import eq_

from lib.sellers.models import Seller, SellerBango
from solitude.base import APITest


class TestPackageResource(APITest):

    def setUp(self):
        super(APITest, self).setUp()
        self.api_name = 'bango'
        self.list_url = self.get_list_url('package')

        p = mock.patch('lib.bango.resources.sudsclient')
        self.sudscli = p.start()
        self.addCleanup(p.stop)

    def data_from_post(self, **kw):
        res = self.client.post(self.list_url, **kw)
        return json.loads(res.content)

    def mock_service(self):
        client = Mock()
        self.sudscli.Client.return_value = client
        return client.service

    def mock_response(self):
        bango = Mock()
        bango.responseCode = 'OK'
        bango.responseMessage = ''
        bango.packageId = 1
        bango.adminPersonId = 2
        bango.supportPersonId = 3
        bango.financePersonId = 4
        self.mock_service().CreatePackage.return_value = bango
        return bango

    def good_data(self):
        return {'adminEmailAddress': 'admin@place.com',
                'supportEmailAddress': 'support@place.com',
                'financeEmailAddress': 'finance@place.com',
                'paypalEmailAddress': 'paypal@place.com',
                'vendorName': 'Some Company',
                'companyName': 'Some Company, LLC',
                'address1': '111 Somewhere',
                'addressCity': 'Pleasantville',
                'addressState': 'CA',
                'addressZipCode': '11111',
                'addressPhone': '4445551111',
                'countryIso': 'USA',
                'currencyIso': 'USD'}

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post'])

    def test_create(self):
        bango = self.mock_response()
        data = self.data_from_post(data=self.good_data())
        seller = Seller.objects.get()
        eq_(data['seller_pk'], seller.pk)
        eq_(data['seller_bango_pk'], seller.bango.pk)

    def test_missing_field(self):
        bango = self.mock_response()
        # Submit missing fields:
        data = {'adminEmailAddress': 'admin@place.com',
                'supportEmailAddress': 'support@place.com'}
        data = self.data_from_post(data=data)
        eq_(data['companyName'], ['This field is required.'])

    def test_bango_fail(self):
        bango = self.mock_response()
        bango.responseCode = 'FAIL'
        bango.responseMessage = 'something happened'
        data = self.data_from_post(data=self.good_data())
        eq_(Seller.objects.all().count(), 0)
        eq_(SellerBango.objects.all().count(), 0)
        eq_(data['response_code'], bango.responseCode)
        eq_(data['response_message'], bango.responseMessage)
