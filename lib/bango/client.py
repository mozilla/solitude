import functools
import json
import os
import re
from time import time

from django.conf import settings

import commonware.log
from django_statsd.clients import statsd
from mock import Mock
from requests import post
from suds import client as sudsclient

from .constants import OK, ACCESS_DENIED, HEADERS_SERVICE
from .errors import AuthError, BangoError

root = os.path.join(settings.ROOT, 'lib/bango/wsdl')
wsdl = {
    'exporter': 'file://' + os.path.join(root, 'mozilla_exporter.wsdl'),
    'billing': 'file://' + os.path.join(root, 'billing_configuration.wsdl'),
}

# Add in the whitelist of supported methods here.
whitelist = [
    'CreatePackage',
    'UpdateSupportEmailAddress',
    'UpdateFinanceEmailAddress',
    'CreateBangoNumber',
    'MakePremiumPerAccess',
    'UpdateRating',
]


# Turn the method into the approiate name. If the Bango WSDL diverges this will
# need to change.
def get_request(name):
    return name + 'Request'


def get_response(name):
    return name + 'Response'


def get_result(name):
    return name + 'Result'


# If we use . in the names we can do queries like update.*
def get_statsd_name(name):
    return re.sub('(?<=\w)(?=[A-Z])', '.', name).lower()


log = commonware.log.getLogger('s.bango')


class Client(object):

    def __getattr__(self, attr):
        if attr in whitelist:
            return functools.partial(self.call, attr)
        raise AttributeError

    def call(self, name, data):
        client = self.client('exporter')
        package = client.factory.create(get_request(name))
        for k, v in data.iteritems():
            setattr(package, k, v)
        package.username = settings.BANGO_AUTH.get('USER', '')
        package.password = settings.BANGO_AUTH.get('PASSWORD', '')

        # Actually call Bango.
        with statsd.timer('solitude.bango.%s' % get_statsd_name(name)):
            response = getattr(client.service, name)(package)

        self.is_error(response.responseCode, response.responseMessage)
        return response

    def client(self, name):
        return sudsclient.Client(wsdl[name])

    def is_error(self, code, message):
        # If there was an error raise it.
        if code == ACCESS_DENIED:
            raise AuthError(ACCESS_DENIED, message)
        elif code != OK:
            raise BangoError(code, message)


class ClientProxy(Client):

    def call(self, name, data):
        with statsd.timer('solitude.proxy.bango.%s' % get_statsd_name(name)):
            log.info('Calling proxy: %s' % name)
            response = post(settings.BANGO_PROXY, data,
                            headers={HEADERS_SERVICE: name,
                                     'Content-Type': 'application/json'},
                            verify=False)
            result = json.loads(response.content)
            self.is_error(result['responseCode'], result['responseMessage'])

            # If it all worked, we need to find a result object and map
            # everything back on to it, so that a result from the proxy
            # looks exactly the same.
            client = self.client('exporter')
            result_obj = getattr(client.factory.create(get_response(name)),
                                 get_result(name))
            for k, v in result.iteritems():
                setattr(result_obj, k, v)
            return result_obj


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
}


class ClientMock(Client):

    def mock_results(self, key):
        result = mock_data.get(key, {}).copy()
        result.update({'responseCode': 'OK',
                       'responseMessage': ''})
        return result

    def call(self, name, data):
        """
        This fakes out the client and just looks up the values in mock_results
        for that service.
        """
        bango = Mock()
        bango.__keylist__ = self.mock_results(name).keys()
        for k, v in self.mock_results(name).iteritems():
            if callable(v):
                v = v()
            setattr(bango, k, v)
        self.is_error(bango.responseCode, bango.responseMessage)
        return bango


def get_client():
    """
    Use this to get the right client and communicate with Bango.
    """
    if settings.BANGO_MOCK:
        return ClientMock()
    if settings.BANGO_PROXY and not settings.SOLITUDE_PROXY:
        return ClientProxy()
    return Client()
