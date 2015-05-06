import uuid

import mock

from lib.brains.errors import MockError
from lib.brains.models import BraintreeBuyer
from lib.buyers.models import Buyer
from solitude.base import APITest


def create_buyer():
    buyer = Buyer.objects.create(uuid=str(uuid.uuid4()))
    braintree_buyer = BraintreeBuyer.objects.create(
        braintree_id='sample:id', buyer=buyer)
    return buyer, braintree_buyer


class BraintreeMock(mock.Mock):

    def __getattr__(self, name):
        """
        Record that a mock method was registered so we can check it
        was called.
        """
        if not name.startswith('_'):
            setattr(self, '_registered', [])
            self._registered.append(name)
        return super(BraintreeMock, self).__getattr__(name)

    def tolist(self, *args, **kw):
        """
        DRF can get into a infinite loop with Mock on this method. If you
        override the mock so it returns a value it works.

        This is a hack of the worst kind.
        """
        raise MockError(
            'Attempt to serialise a Mock without the result being overridden.')


class BraintreeTest(APITest):

    """
    A standard APITest with the ability to provide Braintree mocks.

    Add in dict of gateways to override onto the class, for example:

            gateways = {'client': ClientTokenGateway}

    Access the mock like this:

            self.mocks['client'].generate.return_value = 'a-sample-token'

    This class will throw a MockError if a result is not defined or if a
    result was defined but never called.
    """
    gateways = {}

    def setUp(self):
        super(BraintreeTest, self).setUp()

        self.classes = {}
        self.mocks = {}

        for key, gateway in self.gateways.items():
            name = gateway.__name__
            # Patch all the classes in the gateway.
            patch = mock.patch(
                'braintree.braintree_gateway.' + name, name='gateway.' + name)
            self.classes[key] = patch.start()
            self.classes[key].patcher = patch

            # When the classes in the gateway are called, patch the returning
            # object to be a mock based off the spec. Doing this prevents
            # typos on the mock.
            obj = BraintreeMock(
                name='gateway.object.' + name, spec=gateway)
            self.classes[key].return_value = obj
            self.mocks[key] = obj

        self.addCleanup(self.cleanUpBrains)

    def cleanUpBrains(self):
        # Stop the class mocks.
        for v in self.classes.values():
            v.patcher.stop()

        # Check that each object mock that was registered was called.
        for k, v in self.mocks.items():
            for call in getattr(v, '_registered', []):
                if not getattr(v, call).called:
                    raise MockError('{0}.{1} registered but not called.'
                                    .format(self.gateways[k].__name__, call))
