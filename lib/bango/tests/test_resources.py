import json

from django.conf import settings

import mock
from mock import Mock
from nose.tools import eq_

from lib.sellers.models import Seller, SellerBango
from solitude.base import APITest

from ..client import ClientMock
from ..errors import BangoError
from .samples import good_address


@mock.patch.object(settings, 'BANGO_MOCK', True)
class TestPackageResource(APITest):

    def setUp(self):
        super(APITest, self).setUp()
        self.api_name = 'bango'
        self.uuid = 'foo:uuid'
        self.list_url = self.get_list_url('package')

    def data_from_post(self, **kw):
        res = self.client.post(self.list_url, **kw)
        return json.loads(res.content)

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post'])

    def test_create(self):
        data = self.data_from_post(data=good_address)
        seller_bango = SellerBango.objects.get()
        eq_(data['resource_pk'], seller_bango.pk)

    def test_missing_field(self):
        data = {'adminEmailAddress': 'admin@place.com',
                'supportEmailAddress': 'support@place.com'}
        data = self.data_from_post(data=data)
        eq_(data['companyName'], ['This field is required.'])

    # TODO: probably should inject this in a better way.
    @mock.patch.object(ClientMock, 'mock_results')
    def test_bango_fail(self, mock_results):
        mock_results.return_value = {'responseCode': 'FAIL'}
        res = self.client.post(self.list_url, data=good_address)
        eq_(res.status_code, 500)

    def create(self):
        seller = Seller.objects.create(uuid=self.uuid)
        seller_bango = SellerBango.objects.create(seller=seller,
                            package_id=1, admin_person_id=3,
                            support_person_id=3, finance_person_id=4)
        return seller_bango

    def test_get_allowed(self):
        seller_bango = self.create()
        url = self.get_detail_url('package', seller_bango.pk)
        self.allowed_verbs(url, ['get', 'patch'])

    def test_get(self):
        seller_bango = self.create()
        url = self.get_detail_url('package', seller_bango.pk)
        seller_bango = SellerBango.objects.get()
        data = json.loads(self.client.get(url).content)
        eq_(data['resource_pk'], seller_bango.pk)

    def test_patch(self):
        seller_bango = self.create()
        url = self.get_detail_url('package', seller_bango.pk)
        seller_bango = SellerBango.objects.get()
        old_support = seller_bango.support_person_id
        old_finance = seller_bango.finance_person_id

        res = self.client.patch(url, data={'supportEmailAddress':'a@a.com'})
        eq_(res.status_code, 202)
        seller_bango = SellerBango.objects.get()

        # Check that support changed, but finance didn't.
        assert seller_bango.support_person_id != old_support
        assert seller_bango.finance_person_id == old_finance
