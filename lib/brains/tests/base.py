import uuid
from StringIO import StringIO

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import mock
import requests
from braintree.error_result import ErrorResult
from nose.plugins.attrib import attr
from payments_config import populate

from lib.brains.errors import MockError
from lib.brains.models import (
    BraintreeBuyer, BraintreePaymentMethod, BraintreeSubscription)
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
    return Buyer.objects.create(
        uuid=str(uuid.uuid4()), email='email@example.com')


def create_method(braintree_buyer):
    return BraintreePaymentMethod.objects.create(
        braintree_buyer=braintree_buyer,
        provider_id=str(uuid.uuid4()),
        type=PAYMENT_METHOD_CARD)


def create_seller(seller_product_data=None):
    seller = Seller.objects.create(uuid=str(uuid.uuid4()))
    data = {
        'external_id': str(uuid.uuid4()),
        'public_id': 'moz-brick',
        'seller': seller
    }
    data.update(seller_product_data or {})
    seller_product = SellerProduct.objects.create(**data)
    return seller, seller_product


def create_subscription(paymethod, seller_product):
    return BraintreeSubscription.objects.create(
        paymethod=paymethod,
        provider_id=str(uuid.uuid4()),
        seller_product=seller_product,
    )


def error(errors=None):
    errors = {'scope': {'errors': errors or []}}
    return ErrorResult(None, {'errors': errors, 'message': ''})


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


class ProductsTest(APITest):

    """
    A test that wraps the products from payments-config so that
    tests do not have to be dependent upon the content in payments-config.
    """
    product_config = {
        'moz': {
            'email': 'support@concrete.mozilla.org',
            'name': 'Mozilla Concrete',
            'url': 'http://pay.dev.mozaws.net/',
            'terms': 'http://pay.dev.mozaws.net/terms/',
            'kind': 'products',
            'products': [{
                'id': 'brick',
                'description': 'Recurring',
                'amount': '10.00',
                'recurrence': 'monthly',
            }],
        }
    }

    def setUp(self):
        super(ProductsTest, self).setUp()

        products = mock.patch('payments_config.products', name='products')
        self.product_mock = products.start()
        self.product_mock.get = populate(self.product_config)[1].get

        self.product_mock.patcher = products
        self.addCleanup(self.product_mock.patcher.stop)


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

        self.addCleanup(self.clean_up_brains)

    def clean_up_brains(self):
        # Stop the class mocks.
        for v in self.classes.values():
            v.patcher.stop()

        # Check that each object mock that was registered was called.
        for k, v in self.mocks.items():
            for call in getattr(v, '_registered', []):
                if not getattr(v, call).called:
                    raise MockError('{0}.{1} registered but not called.'
                                    .format(self.gateways[k].__name__, call))

    def clean_up_request(self):
        self.req.patcher.stop()

    def patch_webhook_forms(self):
        request = mock.patch('lib.brains.forms.requests', name='test.forms')
        self.req = request.start()
        self.req.exceptions = requests.exceptions
        self.req.patcher = request
        self.addCleanup(self.clean_up_request)

    def get_response(self, data, status_code, headers=None):
        headers = headers or {}
        raw = StringIO()
        raw.write(data)
        raw.seek(0)

        res = requests.Response()
        res.status_code = status_code
        res.raw = raw
        res.headers.update(headers)
        return res


@attr('braintree')
class BraintreeLiveTestCase(LiveTestCase):

    def setUp(self):
        for key in ['BRAINTREE_MERCHANT_ID',
                    'BRAINTREE_PUBLIC_KEY',
                    'BRAINTREE_PRIVATE_KEY']:
            if not getattr(settings, key):
                raise ImproperlyConfigured('{0} is empty'.format(key))

        super(LiveTestCase, self).setUp()
