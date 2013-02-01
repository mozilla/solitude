from datetime import datetime
import functools
import os
import uuid
from time import time

from django.conf import settings

import commonware.log
from django_statsd.clients import statsd
from mock import Mock
from requests import post
from suds import client as sudsclient
from suds.transport import Reply
from suds.transport.http import HttpTransport

from .constants import OK, ACCESS_DENIED, HEADERS_SERVICE
from .errors import AuthError, BangoError

root = os.path.join(settings.ROOT, 'lib', 'bango', 'wsdl', settings.BANGO_ENV)
wsdl = {
    'exporter': 'file://' + os.path.join(root, 'mozilla_exporter.wsdl'),
    'billing': 'file://' + os.path.join(root, 'billing_configuration.wsdl'),
    'direct': 'file://' + os.path.join(root, 'direct_billing.wsdl'),
}

# Add in the whitelist of supported methods here.
exporter = [
    'AcceptSBIAgreement',
    'CreateBangoNumber',
    'CreateBankDetails',
    'CreatePackage',
    'GetAcceptedSBIAgreement',
    'GetPackage',
    'GetSBIAgreement',
    'MakePremiumPerAccess',
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


# Turn the method into the approiate name. If the Bango WSDL diverges this will
# need to change.
def get_request(name):
    return name + 'Request'


def get_response(name):
    return name + 'Response'


def get_result(name):
    return name + 'Result'


log = commonware.log.getLogger('s.bango')


class Client(object):

    def __getattr__(self, attr):
        for name, methods in (['exporter', exporter],
                              ['billing', billing],
                              ['direct', direct]):
            if attr in methods:
                return functools.partial(self.call, attr, wsdl=str(name))
        raise AttributeError('Unknown request: %s' % attr)

    def call(self, name, data, wsdl='exporter'):
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
        return sudsclient.Client(wsdl[name])

    def is_error(self, code, message):
        # Count the numbers of responses we get.
        statsd.incr('solitude.bango.response.%s' % code.lower())
        # If there was an error raise it.
        if code == ACCESS_DENIED:
            raise AuthError(ACCESS_DENIED, message)
        elif code != OK:
            raise BangoError(code, message)


class Proxy(HttpTransport):

    def send(self, request):
        response = post(settings.BANGO_PROXY,
                data=request.message,
                headers={HEADERS_SERVICE: request.url},
            verify=False)
        return Reply(response.status_code, {}, response.content)


class ClientProxy(Client):

    def client(self, name):
        return sudsclient.Client(wsdl[name], transport=Proxy())


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
        'billingConfigurationId': uuid.uuid4
    },
    'GetAcceptedSBIAgreement': {
        'sbiAgreementAccepted': True,
        'acceptedSBIAgreement': '2013-01-23 00:00:00',
        'sbiAgreementExpires': '2014-01-23 00:00:00'
    },
    'GetSBIAgreement': {
        'sbiAgreement': 'Blah...',
        'sbiAgreementValidFrom': '2010-08-31 00:00:00',
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
    }
}


class ClientMock(Client):

    def mock_results(self, key):
        result = mock_data.get(key, {}).copy()
        result.update({'responseCode': 'OK',
                       'responseMessage': ''})
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
