import json

from django.conf import settings

import mock
from mock import Mock
from nose.tools import eq_

from lib.sellers.models import Seller
from solitude.base import APITest

from ..client import ClientMock
from ..errors import BangoError
from .samples import good_address


@mock.patch.object(settings, 'BANGO_MOCK', True)
class TestPackageResource(APITest):

    def setUp(self):
        super(APITest, self).setUp()
        self.api_name = 'bango'
        self.list_url = self.get_list_url('package')

    def data_from_post(self, **kw):
        res = self.client.post(self.list_url, **kw)
        return json.loads(res.content)

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post'])

    def test_create(self):
        data = self.data_from_post(data=good_address)
        seller = Seller.objects.get()
        eq_(data['seller_pk'], seller.pk)
        eq_(data['seller_bango_pk'], seller.bango.pk)

    def test_missing_field(self):
        data = {'adminEmailAddress': 'admin@place.com',
                'supportEmailAddress': 'support@place.com'}
        data = self.data_from_post(data=data)
        eq_(data['companyName'], ['This field is required.'])

    # TODO: probably should inject this in a better way.
    @mock.patch.object(ClientMock, 'mock_results')
    def test_bango_fail(self, mock_results):
        mock_results.return_value = {'responseCode': 'FAIL'}
        res =  self.client.post(self.list_url, data=good_address)
        eq_(res.status_code, 500)
