from lib.brains.client import get_client, Http
from lib.brains.tests.base import BraintreeTest


class TestClient(BraintreeTest):

    def test_normal(self):
        with self.settings(BRAINTREE_PRIVATE_KEY='test-key'):
            assert isinstance(
                get_client().Configuration.instantiate()._http_strategy,
                Http)
