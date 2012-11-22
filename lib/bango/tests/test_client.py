# -*- coding: utf-8 -*-
import json

import mock
from nose.tools import eq_
import test_utils

from ..client import get_client, Client, ClientMock, ClientProxy
from ..constants import OK, ACCESS_DENIED
from ..errors import AuthError, BangoError

from .samples import good_address, good_email


class TestClient(test_utils.TestCase):

    def setUp(self):
        with self.settings(BANGO_MOCK=True):
            self.client = get_client()

    def test_create_package(self):
        res = self.client.CreatePackage(good_address)
        eq_(res.responseCode, OK)
        eq_(res.packageId, 1)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_auth_failure(self, mock_results):
        mock_results.return_value = {'responseCode': ACCESS_DENIED}
        with self.assertRaises(AuthError):
            self.client.CreatePackage(good_address)

    @mock.patch.object(ClientMock, 'mock_results')
    def test_failure(self, mock_results):
        mock_results.return_value = {'responseCode': 'wat'}
        with self.assertRaises(BangoError):
            self.client.CreatePackage(good_address)

    def test_update_support_email(self):
        res = self.client.UpdateSupportEmailAddress(good_email)
        eq_(res.responseCode, OK)

    def test_update_financial_email(self):
        res = self.client.UpdateFinancialEmailAddress(good_email)
        eq_(res.responseCode, OK)


class TestRightClient(test_utils.TestCase):

    def test_no_proxy(self):
        with self.settings(BANGO_PROXY=None, SOLITUDE_PROXY=False):
            assert isinstance(get_client(), Client)

    def test_using_proxy(self):
        with self.settings(BANGO_PROXY='http://foo.com'):
            assert isinstance(get_client(), ClientProxy)

    def test_am_proxy(self):
        with self.settings(BANGO_PROXY='http://foo.com', SOLITUDE_PROXY=True):
            assert isinstance(get_client(), Client)

    def test_mock(self):
        with self.settings(BANGO_MOCK=True):
            assert isinstance(get_client(), ClientMock)


class TestProxy(test_utils.TestCase):

    def setUp(self):
        self.bango = ClientProxy()
        self.url = 'http://foo.com'

    @mock.patch('lib.bango.client.post')
    def test_call(self, post):
        resp = mock.Mock()
        resp.status_code = 200
        resp.content = json.dumps({'responseCode': OK,
                                   'responseMessage': 'oops'})
        post.return_value = resp
        with self.settings(BANGO_PROXY=self.url):
            self.bango.CreatePackage({'foo': 'bar'})

        args = post.call_args
        eq_(args[0][0], self.url)
        eq_(args[0][1], {'foo': 'bar'})
        eq_(args[1]['headers']['x-solitude-service'], 'create-package')

    @mock.patch('lib.bango.client.post')
    def test_failure(self, post):
        resp = mock.Mock()
        resp.status_code = 500
        resp.content = json.dumps({'responseCode': 'wat',
                                   'responseMessage': 'oops'})
        post.return_value = resp
        with self.settings(BANGO_PROXY=self.url):
            with self.assertRaises(BangoError):
                self.bango.CreatePackage({'foo': 'bar'})

    @mock.patch('lib.bango.client.post')
    def test_ok(self, post):
        resp = mock.Mock()
        resp.status_code = 200
        resp.content = json.dumps({'responseCode': OK,
                                   'responseMessage': '',
                                   'packageId': 1})
        post.return_value = resp
        with self.settings(BANGO_PROXY=self.url):
            res = self.bango.CreatePackage({'foo': 'bar'})
            eq_(res.packageId, 1)
            assert 'CreatePackageResponse' in str(res)
