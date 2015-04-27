from lib.brains.client import set_mocks
from solitude.base import APITest


class BraintreeTest(APITest):

    def setUp(self):
        self.set_mocks = set_mocks
        super(BraintreeTest, self).setUp()

    def tearDown(self):
        set_mocks()
        super(BraintreeTest, self).tearDown()
