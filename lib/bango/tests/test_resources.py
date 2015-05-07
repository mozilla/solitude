# -*- coding: utf-8 -*-
import contextlib
import json
from hashlib import md5

from django import test
from django.conf import settings
from django.core.urlresolvers import reverse

import mock
from nose.tools import eq_, ok_

import samples
import utils
from ..client import ClientMock
from ..constants import (ALREADY_REFUNDED, BANGO_ALREADY_PREMIUM_ENABLED,
                         CANT_REFUND, INTERNAL_ERROR, MICRO_PAYMENT_TYPES, OK,
                         PAYMENT_TYPES, PENDING, SBI_ALREADY_ACCEPTED,
                         STATUS_BAD, STATUS_GOOD)
from ..errors import BangoError
from lib.bango.views.base import BangoResource
from lib.bango.views.refund import RefundViewSet
from lib.bango.views.status import Status, StatusSerializer
from lib.buyers.models import Buyer
from lib.sellers.models import (Seller, SellerBango, SellerProduct,
                                SellerProductBango)
from lib.transactions import constants
from lib.transactions.constants import (PROVIDER_BANGO, PROVIDER_REFERENCE,
                                        STATUS_CANCELLED, STATUS_COMPLETED,
                                        STATUS_PENDING, TYPE_REFUND,
                                        TYPE_REFUND_MANUAL)
from lib.transactions.models import Transaction
from solitude.base import APITest
from solitude.constants import PAYMENT_METHOD_ALL, PAYMENT_METHOD_OPERATOR


class BangoAPI(APITest):
    api_name = 'bango'
    uuid = 'foo:uuid'

    def create(self, without_product_bango=False):
        """
        The `without_product_bango` boolean is useful to test
        `SellerProductBango` objects creation and duplicates.
        """
        self.buyer = Buyer.objects.create(
            uuid=samples.good_billing_request['user_uuid'])
        self.sellers = utils.make_sellers(uuid=self.uuid)
        self.seller = self.sellers.seller
        self.seller_bango = self.sellers.bango
        self.seller_product = self.sellers.product
        if without_product_bango:
            self.sellers.product_bango.delete()
        self.seller_bango_uri = self.seller_bango.get_uri()
        self.seller_product_uri = self.seller_product.get_uri()
        # Not sure why this is the same as seller bango uri.
        self.package_uri = self.seller_bango.get_uri()


class TestError(APITest):

    def test_form_error(self):
        class Foo(BangoResource):
            error_lookup = {'INVALID': 'name'}

        class Error(object):

            def __init__(self, id, message):
                self.id = id
                self.message = message

        foo = Foo()
        # Got the lookup right.
        eq_(foo.client_errors(Error('foo', 'bar')).errors,
            {'__all__': ['bar'], '__type__': 'bango', '__bango__': 'foo'})

        # Got the lookup wrong.
        eq_(foo.client_errors(Error('INVALID', 'thing!')).errors,
            {'name': ['thing!'], '__type__': 'bango', '__bango__': 'INVALID'})


class TestLoginResource(BangoAPI):

    def setUp(self):
        super(TestLoginResource, self).setUp()
        self.login_url = reverse('bango:bango.login')
        self.overrides = {}

    def test_nodata(self):
        res = self.client.post(self.login_url, data={})
        eq_(res.status_code, 400, res.status_code)
        eq_(res.json,
            {u'packageId': [u'This field is required.']})

    @mock.patch.object(ClientMock, 'mock_results')
    def test_invalid_package(self, mock_results):
        self.overrides['GetEmailAddresses'] = {
            'responseCode': 'INVALID_PACKAGEID',
            'responseMessage': 'wat'
        }
        mock_results.side_effect = self.variable
        res = self.client.post(self.login_url, data={'packageId': 1})
        eq_(res.status_code, 400, res.content)
        eq_(self.get_errors(res.content, '__all__'), ['wat'])

    def variable(self, mthd):
        result = {
            'GetEmailAddresses': {
                'adminEmailAddress': 'admin@example.org',
                'adminPersonId': 1234,
                'responseCode': 'OK'
            },
            'GetAutoAuthenticationLoginToken': {
                'authenticationToken': 'foo',
                'responseCode': 'OK'
            }
        }
        result.update(self.overrides)
        return result[mthd]

    @mock.patch.object(ClientMock, 'mock_results')
    def test_invalid_person(self, mock_results):
        self.overrides['GetAutoAuthenticationLoginToken'] = {
            'responseCode': 'INVALID_PERSON',
            'responseMessage': 'wat'
        }
        mock_results.side_effect = self.variable

        res = self.client.post(self.login_url, data={'packageId': 1})
        eq_(res.status_code, 400, res.content)
        eq_(self.get_errors(res.content, '__all__'), ['wat'])

    @mock.patch.object(ClientMock, 'mock_results')
    def test_good(self, mock_results):
        mock_results.side_effect = self.variable

        res = self.client.post(self.login_url, data={'packageId': 1})
        eq_(res.status_code, 200, res.content)
        data = res.json
        eq_(data[u'email_address'], u'admin@example.org')
        eq_(data[u'authentication_token'], u'foo')
        eq_(data[u'person_id'], 1234)


class TestPackageResource(BangoAPI):

    def setUp(self):
        super(TestPackageResource, self).setUp()
        self.list_url = reverse('bango:package-list')

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['get', 'post'])

    def test_create(self):
        res = self.client.post(self.list_url, data=self.good_data())
        eq_(res.status_code, 201, res.content)
        seller_bango = SellerBango.objects.get()
        eq_(res.json['resource_pk'], seller_bango.pk)

    @mock.patch.object(ClientMock, 'call')
    def test_insert(self, call):
        with self.settings(BANGO_INSERT_STAGE='STAGE '):
            self.client.post(self.list_url, data=self.good_data())

        data = call.call_args[0][1]
        eq_(data['vendorName'], 'STAGE Some Company')
        eq_(data['companyName'], 'STAGE Some Company, LLC')

    def good_data(self):
        post = samples.good_address.copy()
        post['seller'] = ('/generic/seller/%s/' %
                          Seller.objects.get_or_create(uuid=self.uuid)[0].pk)
        return post

    @mock.patch.object(ClientMock, 'mock_results')
    def test_invalid_country(self, mock_results):
        mock_results.return_value = {'responseCode': 'INVALID_COUNTRYISO',
                                     'responseMessage': 'wat'}
        res = self.client.post(self.list_url, data=self.good_data())
        eq_(res.status_code, 400, res.content)
        eq_(self.get_errors(res.content, 'countryIso'), ['wat'])

    @mock.patch.object(ClientMock, 'mock_results')
    def test_invalid_parameter(self, mock_results):
        mock_results.return_value = {'responseCode': 'INVALID_PARAMETER',
                                     'responseMessage': 'wat'}
        res = self.client.post(self.list_url, data=self.good_data())
        eq_(res.status_code, 400, res.content)
        eq_(self.get_errors(res.content, '__all__'), ['wat'])

    def test_unicode(self):
        post = samples.good_address.copy()
        post['companyName'] = u'འབྲུག་ཡུལ།'
        post['seller'] = ('/generic/seller/%s/' %
                          Seller.objects.create(uuid=self.uuid).pk)
        res = self.client.post(self.list_url, data=post)
        eq_(res.status_code, 201, res.content)

    def test_missing_field(self):
        data = {'adminEmailAddress': 'admin@place.com',
                'supportEmailAddress': 'support@place.com'}
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400, res.content)
        eq_(res.json['companyName'],
            ['This field is required.'])

    def test_get_allowed(self):
        self.create()
        self.allowed_verbs(self.seller_bango.get_uri(), ['get', 'patch'])

    def test_get(self):
        self.create()
        seller_bango = SellerBango.objects.get()
        data = self.client.get(self.package_uri).json
        eq_(data['resource_pk'], seller_bango.pk)
        eq_(data['full'], {})

    def test_get_generic(self):
        self.create()
        data = self.client.get(self.seller.get_uri()).json
        eq_(data['bango']['resource_pk'], self.seller_bango.pk)

    def patch_data(self):
        return {'supportEmailAddress': 'a@a.com',
                'financeEmailAddress': 'a@a.com',
                'address1': '123 Main St.',
                'addressCity': 'Vancouver',
                'addressPhone': '1234567890',
                'addressState': 'BC',
                'addressZipCode': '123456',
                'countryIso': 'AFG',
                'vendorName': 'Vendor',
                'vatNumber': '123'}

    def ok(self):
        return {'responseCode': 'OK',
                'responseMessage': '',
                'personId': '1'}

    def test_patch_emails(self):
        self.create()

        seller_bango = SellerBango.objects.get()
        old_support = seller_bango.support_person_id
        old_finance = seller_bango.finance_person_id

        res = self.client.patch(self.package_uri, data=self.patch_data())
        eq_(res.status_code, 201, res.content)

        seller_bango = seller_bango.reget()
        ok_(seller_bango.support_person_id != old_support)
        ok_(seller_bango.finance_person_id != old_finance)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_patch_invalid(self, mock_results):
        def error(*args, **kwargs):
            if args[0] in ('UpdateFinanceEmailAddress',
                           'UpdateSupportEmailAddress'):
                return {'responseCode': 'INVALID_PERSON',
                        'responseMessage': 'blah'}
            return self.ok()

        mock_results.side_effect = error
        self.create()

        seller_bango = SellerBango.objects.get()
        old_support = seller_bango.support_person_id
        old_finance = seller_bango.finance_person_id

        res = self.client.patch(self.package_uri, data=self.patch_data())
        eq_(res.status_code, 201, (res.status_code, res.content))

        seller_bango = seller_bango.reget()
        eq_(seller_bango.support_person_id, old_support)
        eq_(seller_bango.finance_person_id, old_finance)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_no_vat(self, mock_results):
        def error(*args, **kwargs):
            if args[0] in 'DeleteVATNumber':
                return {'responseCode': 'VAT_NUMBER_DOES_NOT_EXIST',
                        'responseMessage': 'blah'}
            return self.ok()
        mock_results.side_effect = error
        self.create()

        res = self.client.patch(self.package_uri, data=self.patch_data())
        eq_(res.status_code, 201, res.content)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_delete_vat(self, mock_results):
        mock_results.return_value = {'responseCode': 'OK',
                                     'responseMessage': '',
                                     'personId': '1'}
        data = self.patch_data()
        data['vatNumber'] = ''
        self.create()
        res = self.client.patch(self.package_uri, data=data)
        eq_(res.status_code, 201, res.content)
        eq_([c[0][0] for c in mock_results.call_args_list],
            ['UpdateFinanceEmailAddress', 'UpdateSupportEmailAddress',
             'UpdateAddressDetails', 'DeleteVATNumber'])

    @mock.patch.object(ClientMock, 'mock_results')
    def test_methods_called(self, mock_results):
        mock_results.return_value = self.ok()
        self.create()
        res = self.client.patch(self.package_uri, data=self.patch_data())
        eq_(res.status_code, 201, res.content)
        eq_([c[0][0] for c in mock_results.call_args_list],
            ['UpdateFinanceEmailAddress', 'UpdateSupportEmailAddress',
             'UpdateAddressDetails', 'SetVATNumber'])

    def test_get_full(self):
        self.create()
        url = self.seller_bango.get_uri()
        res = self.client.get_with_body(url, data={'full': True})
        data = res.json
        eq_(data['full']['countryIso'], 'BMU')


class TestBangoProduct(BangoAPI):

    def setUp(self):
        super(TestBangoProduct, self).setUp()
        self.list_url = reverse('bango:product-list')

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post', 'get'])

    def test_create(self):
        self.create(without_product_bango=True)
        data = samples.good_bango_number
        data['seller_product'] = ('/generic/product/%s/' %
                                  self.seller_product.pk)
        data['seller_bango'] = self.seller_bango_uri
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 201, res.content)

        obj = SellerProductBango.objects.get()
        eq_(obj.bango_id, 'some-bango-number')
        eq_(obj.seller_product_id, self.seller_product.pk)
        eq_(obj.seller_bango_id, self.seller_bango.pk)

    def test_create_multiple(self):
        # Just a generic test to ensure that multiple posts are 400.
        self.create(without_product_bango=True)
        data = samples.good_bango_number
        data['seller_product'] = ('/generic/product/%s/' %
                                  self.seller_product.pk)
        data['seller_bango'] = self.seller_bango_uri
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 201, res.content)
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400, res.content)

    def test_get_by_seller_product(self):
        self.create()

        # This is a decoy product that should be ignored by the filter.
        pr = SellerProduct.objects.create(seller=self.seller,
                                          external_id='decoy-product',
                                          public_id='uuid')
        SellerProductBango.objects.create(seller_product=pr,
                                          seller_bango=self.seller_bango,
                                          bango_id='999999')

        # We should only fetch the product created in dynamic fixtures.
        res = self.client.get(self.list_url, {
            'seller_product__seller': self.seller.pk,
            'seller_product__external_id': self.seller_product.external_id
        })

        eq_(res.status_code, 200, res.content)
        eq_(res.json['meta']['total_count'], 1, res.json)
        eq_(res.json['objects'][0]['bango_id'], 'sample:bangoid')


class SellerProductBangoBase(BangoAPI):

    def create(self):
        super(SellerProductBangoBase, self).create()
        self.seller_product_bango = self.sellers.product_bango
        self.seller_product_bango_uri = ('/bango/product/%s/' %
                                         self.seller_product_bango.pk)


class TestBangoMarkPremium(SellerProductBangoBase):

    def setUp(self):
        super(TestBangoMarkPremium, self).setUp()
        self.list_url = reverse('bango:premium')

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post'])

    def create(self):
        super(TestBangoMarkPremium, self).create()
        data = samples.good_make_premium.copy()
        data['seller_product_bango'] = self.seller_product_bango_uri
        return data

    def test_mark(self):
        res = self.client.post(self.list_url, data=self.create())
        eq_(res.status_code, 200)

    def test_fail(self):
        data = self.create()
        data['currencyIso'] = 'FOO'
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)

    def test_no_bango(self):
        data = self.create()
        self.seller_product_bango.bango_id = ''
        self.seller_product_bango.save()

        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)
        eq_(self.get_errors(res.content, 'seller_product_bango'),
            [u'Empty bango_id for: %s' % self.seller_product_bango.pk])

    @mock.patch.object(ClientMock, 'mock_results')
    def test_other_error(self, mock_results):
        data = self.create()
        mock_results.return_value = {'responseCode': 'wat?',
                                     'responseMessage': ''}
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_done_twice(self, mock_results):
        data = self.create()
        mock_results.return_value = {'responseCode':
                                     BANGO_ALREADY_PREMIUM_ENABLED,
                                     'responseMessage': ''}
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 204)


class TestBangoUpdateRating(SellerProductBangoBase):

    def test_list_allowed(self):
        self.allowed_verbs(self.list_url, ['post'])

    def setUp(self):
        super(TestBangoUpdateRating, self).setUp()
        self.list_url = reverse('bango:rating')

    def test_update(self):
        self.create()
        data = samples.good_update_rating.copy()
        data['seller_product_bango'] = self.seller_product_bango_uri
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 200, res.content)

    def test_fail(self):
        self.create()
        data = samples.good_update_rating.copy()
        data['rating'] = 'AWESOME!'
        data['seller_product_bango'] = self.seller_product_bango_uri
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400, res.content)

    def test_no_bango(self):
        self.create()
        data = samples.good_update_rating.copy()
        data['seller_product_bango'] = self.seller_product_bango_uri
        self.seller_product_bango.bango_id = ''
        self.seller_product_bango.save()

        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400, (res.status_code, res.content))
        eq_(self.get_errors(res.content, 'seller_product_bango'),
            [u'Empty bango_id for: %s' % self.seller_product_bango.pk])


class TestCreateBillingConfiguration(SellerProductBangoBase):

    def setUp(self):
        super(TestCreateBillingConfiguration, self).setUp()
        self.list_url = reverse('bango:billing')

    def create(self):
        super(TestCreateBillingConfiguration, self).create()
        self.transaction = Transaction.objects.create(
            provider=constants.PROVIDER_BANGO,
            seller=self.seller,
            seller_product=self.seller_product,
            status=constants.STATUS_RECEIVED,
            uuid=self.uuid)

    def good(self):
        self.create()
        data = samples.good_billing_request.copy()
        data['seller_product_bango'] = self.seller_product_bango_uri
        data['transaction_uuid'] = self.transaction.uuid
        return data

    @contextlib.contextmanager
    def fake_client_response(self, client):
        client.return_value = mock.Mock(responseCode=200,
                                        responseMessage='OK',
                                        billingConfigurationId=1234)
        yield

    def test_good(self):
        res = self.client.post(self.list_url, data=self.good())
        eq_(res.status_code, 200, res.content)
        assert 'billingConfigurationId' in res.json
        assert 'application_size' not in res.json

    @mock.patch('lib.bango.views.base.BangoResource.client')
    def test_micro_payment_cannot_use_card(self, cli):
        data = self.good()
        data['prices'] = [
            {'price': 0.88, 'currency': 'CAD',
             'method': PAYMENT_METHOD_OPERATOR},
            {'price': 0.98, 'currency': 'USD',
             'method': PAYMENT_METHOD_OPERATOR},
        ]
        with self.fake_client_response(cli):
            res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 200, res.content)
        eq_(sorted(list(cli.call_args[0][1]['typeFilter'].string)),
            sorted(list(MICRO_PAYMENT_TYPES)))

    @mock.patch('lib.bango.views.base.BangoResource.client')
    def test_normal_payment_mixed(self, cli):
        data = self.good()
        data['prices'] = [
            {'price': 0.89, 'currency': 'CAD',
             'method': PAYMENT_METHOD_OPERATOR},
            {'price': 0.99, 'currency': 'USD',
             'method': PAYMENT_METHOD_ALL},
        ]
        with self.fake_client_response(cli):
            res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 200, res.content)
        eq_(sorted(list(cli.call_args[0][1]['typeFilter'].string)),
            sorted(list(PAYMENT_TYPES)))

    def test_with_product_icon(self):
        data = self.good()
        data['icon_url'] = 'http://marketplace-cdn.com/icons/1.png'
        with self.settings(BANGO_ICON_URLS=True):
            res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 200, res.content)
        assert 'billingConfigurationId' in res.json

    def test_missing(self):
        data = samples.good_billing_request.copy()
        del data['prices']
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400)
        assert 'prices' in res.json

    def test_missing_success_url(self):
        data = self.good()
        del data['redirect_url_onsuccess']
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400, res)

    def test_missing_error_url(self):
        data = self.good()
        del data['redirect_url_onerror']
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400, res)

    def test_no_transaction(self):
        data = self.good()
        del data['transaction_uuid']
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 400, res)
        assert 'transaction_uuid' in res.json


class TestCreateBankConfiguration(BangoAPI):

    def setUp(self):
        super(TestCreateBankConfiguration, self).setUp()
        self.list_url = reverse('bango:bank')

    def test_bank(self):
        self.create()
        data = samples.good_bank_details.copy()
        data['seller_bango'] = self.seller_bango_uri
        res = self.client.post(self.list_url, data=data)
        eq_(res.status_code, 200, res.content)


class TestGetSBI(BangoAPI):

    def setUp(self):
        self.get_url = self.list_url = reverse('bango:sbi')

    def test_not_there(self):
        res = self.client.get_with_body(
            self.get_url,
            data={'seller_bango': '/some/uri/4/'})
        eq_(res.status_code, 400)

    def test_wrong_url(self):
        res = self.client.get('/bango/sbi/foo/')
        eq_(res.status_code, 404)

    def test_sbi(self):
        self.create()
        res = self.client.get_with_body(
            self.get_url,
            data={'seller_bango': self.seller_bango_uri})
        eq_(res.status_code, 200)
        data = res.json
        # The SBI mock is there.
        ok_('Self-Billing' in data['text'])
        # The en-US terms are present.
        ok_('Bango Developer Terms' in data['text'])
        eq_(data['valid'], '2010-08-31T00:00:00')

    def test_post(self):
        self.create()
        res = self.client.post(
            self.list_url,
            data={'seller_bango': self.seller_bango_uri})
        eq_(res.status_code, 200)
        data = res.json
        eq_(data['accepted'], '2013-01-23 00:00:00')
        eq_(data['expires'], '2014-01-23 00:00:00')
        eq_(str(self.seller_bango.reget().sbi_expires), '2014-01-23 00:00:00')

    @mock.patch.object(ClientMock, 'mock_results')
    def test_post_already(self, mock_results):
        mock_results.return_value = {'responseCode': SBI_ALREADY_ACCEPTED,
                                     'responseMessage': ''}
        self.create()
        self.client.post(self.list_url,
                         data={'seller_bango': self.seller_bango_uri})
        eq_([c[0][0] for c in mock_results.call_args_list],
            ['AcceptSBIAgreement', 'GetAcceptedSBIAgreement'])

    @mock.patch.object(ClientMock, 'mock_results')
    def test_post_fails(self, mock_results):
        mock_results.return_value = {'responseCode': INTERNAL_ERROR,
                                     'responseMessage': ''}
        self.create()
        with self.assertRaises(BangoError):
            self.client.post(self.list_url,
                             data={'seller_bango': self.seller_bango_uri})


class TestRefund(APITest):

    def setUp(self):
        self.api_name = 'bango'
        self.uuid = 'sample:uid'
        self.sellers = utils.make_sellers(self.uuid)
        self.seller = self.sellers.seller
        self.product = self.sellers.product
        self.trans = Transaction.objects.create(
            amount=5, seller_product=self.product,
            provider=constants.PROVIDER_BANGO, uuid=self.uuid,
            status=constants.STATUS_COMPLETED)
        self.url = reverse('bango:refund-list')
        self.seller_bango = self.sellers.bango

    def _status(self, their_status, our_status, data=None, typ=TYPE_REFUND):
        refund_data = {'uuid': self.uuid}
        if data:
            refund_data.update(data)
        res = self.client.post(self.url, data=refund_data)
        eq_(res.status_code, 200, res.content)
        res_data = res.json
        eq_(res_data['status'], their_status)
        assert res_data['uuid'] != self.uuid

        eq_(len(Transaction.objects.all()), 2)
        trans = Transaction.objects.get(pk=res_data['resource_pk'])
        eq_(trans.related.pk, self.trans.pk)
        eq_(trans.type, typ)
        eq_(trans.status, our_status)
        assert trans.uuid

    def test_ok(self):
        self._status(OK, STATUS_COMPLETED)

    def test_ok_manual(self):
        self._status(OK, STATUS_COMPLETED, data={'manual': True},
                     typ=TYPE_REFUND_MANUAL)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_pending(self, mock_results):
        mock_results.return_value = {'responseCode': PENDING,
                                     'responseMessage': 'patience padawan'}
        self._status(PENDING, STATUS_PENDING)

    def _fail(self):
        res = self.client.post(self.url, data={'uuid': self.uuid})
        eq_(res.status_code, 400)
        ok_(self.get_errors(res.content, 'uuid'))

    def test_not_there(self):
        res = self.client.post(self.url, data={'uuid': 0})
        eq_(res.status_code, 404)

    def test_not_bango(self):
        self.trans.provider = PROVIDER_REFERENCE
        self.trans.save()
        self._fail()

    def test_not_complete(self):
        self.trans.status = STATUS_CANCELLED
        self.trans.save()
        self._fail()

    def test_not_payment(self):
        self.trans.type = TYPE_REFUND
        self.trans.save()
        self._fail()

    def test_refunded(self):
        Transaction.objects.create(
            seller_product=self.product,
            related=self.trans, provider=constants.PROVIDER_BANGO,
            status=constants.STATUS_COMPLETED, type=constants.TYPE_REFUND,
            uuid='something', uid_pay='something')
        self._fail()

    @mock.patch.object(ClientMock, 'mock_results')
    def test_already(self, mock_results):
        mock_results.return_value = {'responseCode': ALREADY_REFUNDED,
                                     'responseMessage': 'nice try'}
        res = self.client.post(self.url, data={'uuid': self.uuid})
        eq_(res.status_code, 400)
        # Check we didn't create a transaction.
        eq_(len(Transaction.objects.all()), 1)

    @mock.patch.object(settings, 'BANGO_FAKE_REFUNDS', True)
    def test_fake_ok(self):
        res = self.client.post(
            self.url,
            data={
                'uuid': self.uuid,
                'fake_response': {'responseCode': OK}})
        eq_(res.status_code, 200)

    @mock.patch.object(settings, 'BANGO_FAKE_REFUNDS', True)
    def test_fake_already(self):
        res = self.client.post(
            self.url,
            data={
                'uuid': self.uuid,
                'fake_response': {'responseCode': ALREADY_REFUNDED}})
        eq_(res.status_code, 400)

    @mock.patch.object(settings, 'BANGO_FAKE_REFUNDS', True)
    def test_fake_not_given(self):
        # No fake given, returning the default OK response
        res = self.client.post(self.url, data={'uuid': self.uuid})
        eq_(res.status_code, 200)


class TestRefundStatus(APITest):

    def setUp(self):
        self.api_name = 'bango'
        self.refund_uuid = 'sample:refund'
        self.sellers = utils.make_sellers('sample:uuid')
        self.seller = self.sellers.seller
        self.product = self.sellers.product
        self.refund = Transaction.objects.create(
            amount=5, seller_product=self.product,
            type=constants.TYPE_REFUND,
            provider=constants.PROVIDER_BANGO,
            uuid=self.refund_uuid, uid_pay='asd',
            status=constants.STATUS_COMPLETED)

        self.url = reverse('bango:refund-list')

    def test_get(self):
        res = self.client.get_with_body(self.url,
                                        data={'uuid': self.refund_uuid})
        data = res.json
        eq_(data['status'], OK)

    def test_get_manual(self):
        self.refund.type = TYPE_REFUND_MANUAL
        self.refund.save()

        res = self.client.get_with_body(self.url,
                                        data={'uuid': self.refund_uuid})
        data = res.json
        eq_(data['status'], OK)

    def test_not_refund(self):
        self.refund.type = constants.TYPE_PAYMENT
        self.refund.save()

        res = self.client.get_with_body(self.url,
                                        data={'uuid': self.refund_uuid})
        eq_(res.status_code, 400, (res.status_code, res.content))
        ok_(self.get_errors(res.content, 'uuid'))

    @mock.patch.object(ClientMock, 'mock_results')
    def test_pending(self, mock_results):
        mock_results.return_value = {'responseCode': PENDING,
                                     'responseMessage': 'patience padawan'}
        res = self.client.get_with_body(self.url,
                                        data={'uuid': self.refund.uuid})
        data = res.json
        eq_(data['status'], PENDING)
        eq_(self.refund.reget().status, constants.STATUS_PENDING)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_pending_manual(self, mock_results):
        mock_results.return_value = {'responseCode': PENDING,
                                     'responseMessage': 'patience padawan'}
        self.refund.type = TYPE_REFUND_MANUAL
        self.refund.save()

        res = self.client.get_with_body(self.url,
                                        data={'uuid': self.refund.uuid})
        eq_(res.status_code, 200)
        # This is not pending, because its a manual response and it got
        # ignored.
        eq_(self.refund.reget().status, constants.STATUS_PENDING)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_failed(self, mock_results):
        mock_results.return_value = {'responseCode': CANT_REFUND,
                                     'responseMessage': 'denied padawan'}
        res = self.client.get_with_body(self.url,
                                        data={'uuid': self.refund.uuid})
        data = res.json
        eq_(data['status'], CANT_REFUND)
        eq_(self.refund.reget().status, constants.STATUS_FAILED)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_ok(self, mock_results):
        self.refund.status = constants.STATUS_PENDING
        self.refund.save()
        mock_results.return_value = {'responseCode': OK,
                                     'responseMessage': ''}
        res = self.client.get_with_body(self.url,
                                        data={'uuid': self.refund.uuid})
        data = res.json
        eq_(data['status'], OK)
        eq_(self.refund.reget().status, constants.STATUS_COMPLETED)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_transactions_failures(self, mock_results):
        mock_results.return_value = {'responseCode': CANT_REFUND,
                                     'responseMessage': 'denied padawan'}
        self.client.get_with_body(self.url,
                                  data={'uuid': self.refund.uuid})
        res = self.client.get(reverse('services.failures.transactions'))
        data = res.json
        transaction = data['transactions'][0]
        eq_(transaction['product_id'], self.product.external_id)
        eq_(transaction['id'], self.refund.id)
        eq_(transaction['uid_pay'], self.refund.uid_pay)
        eq_(transaction['uri'],
            u'/generic/transaction/%s/' % self.refund.id)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_no_transactions_failures(self, mock_results):
        res = self.client.get(reverse('services.failures.transactions'))
        data = res.json
        eq_(data['transactions'], [])
        res = self.client.get(reverse('services.failures.statuses'))
        data = res.json
        eq_(data['statuses'], [])

    @mock.patch.object(settings, 'BANGO_FAKE_REFUNDS', True)
    def fake(self, status):
        self.refund.status = constants.STATUS_PENDING
        self.refund.save()
        res = self.client.get_with_body(self.url, data={
            'uuid': self.refund.uuid,
            'fake_response': {'responseCode': status}
        })
        return res

    def test_fake_ok(self):
        res = self.fake(OK)
        eq_(res.json['status'], OK)
        eq_(self.refund.reget().status, constants.STATUS_COMPLETED)

    def test_fake_pending(self):
        res = self.fake(PENDING)
        eq_(res.json['status'], PENDING)
        eq_(self.refund.reget().status, constants.STATUS_PENDING)


class TestResource(test.TestCase):

    def setUp(self):
        self.res = RefundViewSet()

    @mock.patch.object(settings, 'BANGO_FAKE_REFUNDS', False)
    def test_not_faked(self):
        ok_(not self.res.get_client({}))

    @mock.patch.object(settings, 'BANGO_FAKE_REFUNDS', True)
    def test_partially_faked(self):
        res = self.res.get_client({})
        eq_(res.mock_results('foo')['responseCode'], 'OK')

    @mock.patch.object(settings, 'BANGO_FAKE_REFUNDS', True)
    def test_faked(self):
        res = self.res.get_client({'fake_response': {'responseCode': 'foo'}})
        eq_(res.mock_results('foo')['responseCode'], 'foo')


class TestStatus(SellerProductBangoBase):

    def setUp(self):
        super(TestStatus, self).setUp()
        self.url = reverse('bango:status-list')
        self.create()

    def data(self, overrides=None):
        default = {'seller_product_bango': self.seller_product_bango_uri}
        if overrides:
            default.update(overrides)
        return default

    def test_serializer(self):
        serializer = StatusSerializer(data=self.data())
        ok_(serializer.is_valid())

    def test_etags(self):
        status = Status.objects.create(
            seller_product_bango=self.seller_product_bango)
        res = self.client.get(self.url)
        eq_(res.status_code, 200)
        assert 'etag' in res._headers
        eq_(md5(status.etag).hexdigest(),
            res._headers['etag'][1][1:-1])
        etag = res._headers['etag'][1][1:-1]
        res = self.client.get(self.url,
                              HTTP_IF_NONE_MATCH=etag)
        eq_(res.status_code, 304)

    @mock.patch('lib.bango.forms.CreateBillingConfigurationForm.is_valid')
    def test_form_error(self, is_valid):
        is_valid.return_value = False
        res = self.client.post(self.url, data=self.data())
        eq_(res.status_code, 400)
        status = Status.objects.all()[0]
        eq_(status.status, STATUS_BAD)
        eq_(json.loads(status.errors).keys(), ['form.errors'])

    def test_good(self):
        res = self.client.post(self.url, data=self.data())
        eq_(res.status_code, 201, res.content)
        status = Status.objects.all()[0]
        eq_(status.status, STATUS_GOOD)

    @mock.patch('lib.bango.forms.CreateBillingConfigurationForm.is_valid')
    def test_statuses_failures(self, is_valid):
        is_valid.return_value = False
        self.client.post(self.url, data=self.data())
        status_instance = Status.objects.all()[0]
        res = self.client.get(reverse('services.failures.statuses'))
        data = res.json
        status = data['statuses'][0]
        eq_(status['product_id'],
            status_instance.seller_product_bango.seller_product.external_id)
        eq_(status['id'], status_instance.id)
        eq_(status['errors'], status_instance.errors)

    def test_no_statuses_failures(self):
        self.client.post(self.url, data=self.data())
        res = self.client.get(reverse('services.failures.statuses'))
        data = res.json
        eq_(data['statuses'], [])

    @mock.patch.object(ClientMock, 'mock_results')
    def test_bad(self, mock_results):
        mock_results.return_value = {'responseCode': 'NOPE',
                                     'responseMessage': 'wat?'}
        res = self.client.post(self.url, data=self.data())
        eq_(res.status_code, 201, (res.status_code, res.content))
        status = Status.objects.all()[0]
        eq_(status.status, STATUS_BAD)


class TestDebug(SellerProductBangoBase):

    def setUp(self):
        super(TestDebug, self).setUp()
        self.url = reverse('bango:debug-list')
        self.create()

    def data(self, overrides=None):
        default = {'seller_product_bango': self.seller_product_bango_uri}
        if overrides:
            default.update(overrides)
        return default

    def test_good(self):
        res = self.client.get_with_body(self.url, data=self.data())
        eq_(res.status_code, 200, res.content)
        data = res.json
        eq_(data['bango']['last_status'], {})
        eq_(data['bango']['last_transaction'], {})
        eq_(data['bango']['bango_id'], 'sample:bangoid')
        eq_(data['bango']['package_id'], 1)

    def test_full(self):
        status = self.seller_product_bango.status.create(status=STATUS_GOOD)
        trans = self.seller_product.transaction_set.create(
            status=STATUS_PENDING, provider=PROVIDER_BANGO)
        res = self.client.get_with_body(self.url, data=self.data())
        eq_(res.status_code, 200, res.content)
        data = res.json
        eq_(data['bango']['last_status'],
            {'status': STATUS_GOOD, 'url': reverse('bango:status-detail',
                                                   kwargs={'pk': status.pk})})
        eq_(data['bango']['last_transaction'],
            {'status': STATUS_PENDING,
             'url': '/generic/transaction/%s/' % trans.pk})
