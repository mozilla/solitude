import uuid

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import mock
from braintree.error_result import ErrorResult
from nose.plugins.attrib import attr

from lib.brains.errors import MockError
from lib.brains.models import (
    BraintreeBuyer, BraintreePaymentMethod)
from lib.buyers.models import Buyer
from lib.sellers.models import Seller, SellerProduct
from solitude.base import APITest
from solitude.constants import PAYMENT_METHOD_CARD
from solitude.tests.live import LiveTestCase


def create_braintree_buyer(braintree_id='sample:id'):
    buyer = create_buyer()
    braintree_buyer = BraintreeBuyer.objects.create(
        braintree_id=braintree_id, buyer=buyer)
    return buyer, braintree_buyer


def create_buyer():
    return Buyer.objects.create(uuid=str(uuid.uuid4()))


def create_method(braintree_buyer):
    return BraintreePaymentMethod.objects.create(
        braintree_buyer=braintree_buyer,
        provider_id=str(uuid.uuid4()),
        type=PAYMENT_METHOD_CARD)


def create_seller():
    seller = Seller.objects.create(uuid=str(uuid.uuid4()))
    seller_product = SellerProduct.objects.create(
        external_id='brick',
        public_id=str(uuid.uuid4()),
        seller=seller)
    return seller, seller_product


def error():
    return ErrorResult(None, {'errors': {}, 'message': ''})


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


@attr('braintree')
class BraintreeLiveTestCase(LiveTestCase):

    def setUp(self):
        for key in ['BRAINTREE_MERCHANT_ID',
                    'BRAINTREE_PUBLIC_KEY',
                    'BRAINTREE_PRIVATE_KEY']:
            if not getattr(settings, key):
                raise ImproperlyConfigured('{0} is empty'.format(key))

        super(LiveTestCase, self).setUp()
