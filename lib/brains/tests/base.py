from lib.brains import client
from lib.brains.errors import MockError
from solitude.base import APITest


class BraintreeTest(APITest):

    def setUp(self):
        self.set_mocks = client.set_mocks
        super(BraintreeTest, self).setUp()

    def tearDown(self):
        # You defined some mock calls for braintree, but didn't use them all.
        if client.mocks:
            raise MockError('Unused braintree client mock exists: {0}'
                            .format(client.mocks))
        self.set_mocks()
        super(BraintreeTest, self).tearDown()
