from django.test import TestCase

from braintree.exceptions.not_found_error import NotFoundError
from nose.tools import eq_, raises

from lib.brains.client import get_client, Http, HttpMock


class TestClient(TestCase):

    def test_mock_client(self):
        assert isinstance(
            get_client().Configuration.instantiate()._http_strategy,
            HttpMock)

    def test_normal(self):
        with self.settings(BRAINTREE_MOCK=False,
                           BRAINTREE_PRIVATE_KEY='test-key'):
            assert isinstance(
                get_client().Configuration.instantiate()._http_strategy,
                Http)

    @raises(NotFoundError)
    def test_not_found(self):
        get_client().Customer.find('does-not-exist')

    def test_found(self):
        eq_(get_client().Customer.find('minimal').id, 'minimal')
