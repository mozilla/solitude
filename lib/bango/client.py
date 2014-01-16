from datetime import datetime
import functools
import os
import uuid
from time import time

from django.conf import settings

from django_statsd.clients import statsd
from mock import Mock
from requests import post
from suds import client as sudsclient
from suds.transport import Reply
from suds.transport.http import HttpTransport

from solitude.logger import getLogger
from .constants import (ACCESS_DENIED, HEADERS_SERVICE, INTERNAL_ERROR,
                        SERVICE_UNAVAILABLE)
from .errors import AuthError, BangoError, BangoFormError, ProxyError


# Add in the whitelist of supported methods here.
exporter = [
    'AcceptSBIAgreement',
    'CreateBangoNumber',
    'CreateBankDetails',
    'CreatePackage',
    'DeleteVATNumber',
    'GetAcceptedSBIAgreement',
    'GetAutoAuthenticationLoginToken',
    'GetEmailAddresses',
    'GetPackage',
    'GetSBIAgreement',
    'MakePremiumPerAccess',
    'SetVATNumber',
    'UpdateAddressDetails',
    'UpdateFinanceEmailAddress',
    'UpdateRating',
    'UpdateSupportEmailAddress',
]

billing = [
    'CreateBillingConfiguration',
]

direct = [
    'DoRefund',
    'GetRefundStatus',
]

token_checker = [
    'CheckToken',
]


# Status codes from the proxy that raise an error and stop processing.
FATAL_PROXY_STATUS_CODES = (404, 500,)

# Most of the names in the WSDL map easily, for example: Foo to FooRequest,
# FooResponse etc. Some do not, this is a map of the exceptions.
def name_map():
    if settings.BANGO_BILLING_CONFIG_V2:
        return {
            'request': {
                'CreateBillingConfiguration':
                'InnerCreateBillingConfigurationRequest',
            }
        }
    else:
        return {'request': {}}


# Map the name of the WSDL into a file. Do this dynamically so that tests
# can mess with this as they need to.
def get_wsdl(name):
    root = os.path.join(settings.ROOT, 'lib/bango/wsdl', settings.BANGO_ENV)
    wsdl = {
        'exporter': 'mozilla_exporter.wsdl',
        'billing': 'billing_configuration.wsdl',
        'direct': 'direct_billing.wsdl',
        'token_checker': 'token_checker.wsdl',
    }
    if settings.BANGO_BILLING_CONFIG_V2:
        wsdl['billing'] = 'billing_configuration_v2_0.wsdl'

    return os.path.join('file://' + os.path.join(root, wsdl[name]))


# Turn the method into the appropriate name. If the Bango WSDL diverges this
# will need to change.
def get_request(name):
    return name_map()['request'].get(name, name + 'Request')


def get_response(name):
    return name_map()['response'].get(name, name + 'Response')


def get_result(name):
    return name_map()['result'].get(name, name + 'Result')


log = getLogger('s.bango')


class Client(object):

    def __getattr__(self, attr):
        for name, methods in (['exporter', exporter],
                              ['billing', billing],
                              ['direct', direct],
                              ['token_checker', token_checker]):
            if attr in methods:
                return functools.partial(self.call, attr, wsdl=str(name))
        raise AttributeError('Unknown request: %s' % attr)

    def call(self, name, data, wsdl='exporter'):
        log.info('Bango client call: {0}, wsdl: {1}, package: {2}'
                 .format(name, wsdl, data.get('packageId', '<none>')))
        client = self.client(wsdl)
        package = client.factory.create(get_request(name))
        for k, v in data.iteritems():
            setattr(package, k, v)
        package.username = settings.BANGO_AUTH.get('USER', '')
        package.password = settings.BANGO_AUTH.get('PASSWORD', '')

        # Actually call Bango.
        with statsd.timer('solitude.bango.request.%s' % name.lower()):
            response = getattr(client.service, name)(package)

        self.is_error(response.responseCode, response.responseMessage)
        return response

    def client(self, name):
        # By default, WSDL files are cached but we use local files so we don't
        # need that.
        return sudsclient.Client(get_wsdl(name), cache=None)

    def is_error(self, code, message):
        # Count the numbers of responses we get.
        statsd.incr('solitude.bango.response.%s' % code.lower())
        # If there was an error raise it.
        if code == ACCESS_DENIED:
            raise AuthError(ACCESS_DENIED, message)

        # These are fatal Bango errors that the data can't really do much
        # about.
        elif code in (INTERNAL_ERROR, SERVICE_UNAVAILABLE):
            raise BangoError(code, message)

        # Assume that all other errors are errors from the data.
        elif code != 'OK':
            raise BangoFormError(code, message)


class Proxy(HttpTransport):

    def send(self, request):
        response = post(settings.BANGO_PROXY,
                        data=request.message,
                        headers={HEADERS_SERVICE: request.url},
                        verify=False)
        if response.status_code in FATAL_PROXY_STATUS_CODES:
            msg = ('Proxy returned: %s from: %s' %
                   (response.status_code, request.url))
            log.error(msg)
            raise ProxyError(msg)

        return Reply(response.status_code, {}, response.content)


class ClientProxy(Client):

    def client(self, name):
        return sudsclient.Client(get_wsdl(name), transport=Proxy())


# Add in your mock method data here. If the method only returns a
# responseCode and a responseMessage, there's no need to add the method.
#
# Use of time() for ints, mean that tests work and so do requests from the
# command line using mock. As long as you don't do them too fast.
ltime = lambda: str(int(time() * 1000000))[8:]
mock_data = {
    'CreateBangoNumber': {
        'bango': 'some-bango-number',
    },
    'CreatePackage': {
        'packageId': ltime,
        'adminPersonId': ltime,
        'supportPersonId': ltime,
        'financePersonId': ltime
    },
    'UpdateSupportEmailAddress': {
        'personId': ltime,
        'personPassword': 'xxxxx',
    },
    'UpdateFinanceEmailAddress': {
        'personId': ltime,
        'personPassword': 'xxxxx',
    },
    'CreateBillingConfiguration': {
        'billingConfigurationId': ltime,
    },
    'GetAcceptedSBIAgreement': {
        'sbiAgreementAccepted': True,
        'acceptedSBIAgreement': '2013-01-23 00:00:00',
        'sbiAgreementExpires': '2014-01-23 00:00:00'
    },
    'GetSBIAgreement': {
        'sbiAgreement': """
Self-Billing Agreement
This is an agreement to a self-billing procedure between:
Bango
Bango .Net Ltd.
5 Westbrook Centre...""",
        # Although its a date, the WSDL has this as a date time.
        'sbiAgreementValidFrom': '2010-08-31T00:00:00',
    },
    'DoRefund': {
        'refundTransactionId': uuid.uuid4
    },
    'GetPackage': {
        'adminEmailAddress': 'admin@email.com',
        'supportEmailAddress': 'support@email.com',
        'financeEmailAddress': 'finance@email.com',
        'paypalEmailAddress': 'paypal@email.com',
        'vendorName': 'Some Vendor',
        'companyName': 'Some Company',
        'address1': 'Address 1',
        'address2': 'Address 2',
        'addressCity': 'City',
        'addressState': 'State',
        'addressZipCode': '90210',
        'addressPhone': '1234567890',
        'addressFax': '1234567890',
        'vatNumber': '1234567890',
        'countryIso': 'BMU',
        'currencyIso': 'EUR',
        'homePageURL': 'http://mozilla.org',
        'eventNotificationEnabled': False,
        'eventNotificationURL': '',
        'status': 'LIC',
        'sbiAgreementAccepted': True,
        'acceptedSBIAgreement': datetime.today,
        'sbiAgreementExpires': datetime.today,
    },
    'GetEmailAddresses': {
        'adminPersonId': '123',
        'adminEmailAddress': 'foo@bar.com'
    },
    'GetAutoAuthenticationLoginToken': {
        'authenticationToken': ltime
    }
}


class ClientMock(Client):

    def mock_results(self, key, data=None):
        """
        Returns result for a key. Data can be passed in to override mock_data.
        """
        result = data or mock_data.get(key, {}).copy()
        for key, value in (['responseCode', 'OK'], ['responseMessage', '']):
            if key not in result:
                result[key] = value
        return result

    def call(self, name, data, wsdl=''):
        """
        This fakes out the client and just looks up the values in mock_results
        for that service.
        """
        bango = dict_to_mock(self.mock_results(name), callables=True)
        self.is_error(bango.responseCode, bango.responseMessage)
        return bango


def response_to_dict(resp):
    """Converts a suds response into a dictionary suitable for JSON"""
    return dict((k, getattr(resp, k)) for k in resp.__keylist__)


def dict_to_mock(data, callables=False):
    """
    Converts a dictionary into a suds like mock.
    callables: will call any value if its callable, default False.
    """
    result = Mock()
    result.__keylist__ = data.keys()
    for k, v in data.iteritems():
        if callables and callable(v):
            v = v()
        setattr(result, k, v)
    return result


def get_client():
    """
    Use this to get the right client and communicate with Bango.
    """
    if settings.BANGO_MOCK:
        return ClientMock()
    if settings.BANGO_PROXY:
        return ClientProxy()
    return Client()


class Form(object):
    """A fake form to reformat Bango errors into form errors."""

    def __init__(self, errors):
        self.errors = errors


def format_client_error(key, exc):
    """
    Define error_lookup as a dictionary on a resource. If the error from
    Bango maps to a form field we'll put the error on that form field.
    Otherwise it gets assigned to __all__.
    """
    return Form({key: [exc.message], '__bango__': exc.id, '__type__': 'bango'})
