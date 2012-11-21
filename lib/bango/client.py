import json
import os

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
methods = {
    'create-package': 'CreatePackage',
    'update-support-email': 'UpdateSupportEmail',
    'update-financial-email': 'UpdateFinancialEmail',
}

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

    def CreatePackage(self, data):
        return self.call('create-package', data)

    def UpdateSupportEmailAddress(self, data):
        return self.call('update-support-email', data)

    def UpdateFinancialEmailAddress(self, data):
        return self.call('update-financial-email', data)

    def call(self, name, data):
        client = self.client('exporter')
        method = methods[name]
        package = client.factory.create(get_request(method))
        for k, v in data.iteritems():
            setattr(package, k, v)
        package.username = settings.BANGO_AUTH.get('USER', '')
        package.password = settings.BANGO_AUTH.get('PASSWORD', '')

        # Actually call Bango.
        with statsd.timer('solitude.bango.%s' % name):
            response = getattr(client.service, method)(package)

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
        method = methods[name]
        with statsd.timer('solitude.proxy.bango.%s' % name):
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
            result_obj = getattr(client.factory.create(get_response(method)),
                                 get_result(method))
            for k, v in result.iteritems():
                setattr(result_obj, k, v)
            return result_obj


mock_data = {
    'create-package': {
        'responseCode': 'OK',
        'responseMessage': '',
        'packageId': 1,
        'adminPersonId': 2,
        'supportPersonId': 3,
        'financePersonId': 4
    },
    'update-support-email': {
        'responseCode': 'OK',
        'responseMessage': '',
        'personId': 1,
        'personPassword': 'xxxxx',
    },
    'update-financial-email': {
        'responseCode': 'OK',
        'responseMessage': '',
        'personId': 1,
        'personPassword': 'xxxxx',
    },
}

class ClientMock(Client):

    def mock_results(self, key):
        # This exists for easy mocking. TODO: think of a better way to do this.
        return mock_data[key]

    def call(self, name, data):
        """
        This fakes out the client and just looks up the values in mock_results
        for that service.
        """
        bango = Mock()
        bango.__keylist__ = self.mock_results(name).keys()
        for k, v in self.mock_results(name).iteritems():
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
