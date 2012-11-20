# -*- coding: utf-8 -*-
import mock
from nose.tools import eq_
import test_utils

from ..client import get_client, Client, ClientMock, ClientProxy
from ..constants import OK, ACCESS_DENIED
from ..errors import AuthError, BangoError

from .samples import good_address


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
