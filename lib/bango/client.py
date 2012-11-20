from django.conf import settings

from django_statsd.clients import statsd
from mock import Mock
from suds import client as sudsclient

from .constants import OK, ACCESS_DENIED
from .errors import AuthError, BangoError

domain = 'https://webservices.bango.com/'
wsdl = {
    'exporter': domain + 'mozillaexporter/?WSDL',
    'billing': domain + 'billingconfiguration/?WSDL',
}

requests = {
    'create-package': ['CreatePackageRequest', 'CreatePackage'],
}


class Client(object):

    def CreatePackage(self, data):
        client = sudsclient.Client(wsdl['exporter'])
        response = self.call(client, 'create-package', data)
        return response

    def call(self, client, name, data):
        request, method = requests[name]
        package = client.factory.create(request)
        for k, v in data.iteritems():
            setattr(package, k, v)
        package.username = settings.BANGO_AUTH.get('USER', '')
        package.password = settings.BANGO_AUTH.get('PASSWORD', '')

        # Actually call Bango.
        with statsd.timer('solitude.bango.%s' % method):
            response = getattr(client.service, method)(package)

        self.is_error(response)
        return response

    def is_error(self, response):
        # If there was an error raise it.
        if response.responseCode == ACCESS_DENIED:
            raise AuthError(ACCESS_DENIED, response.responseMessage)
        elif response.responseCode != OK:
            raise BangoError(response.responseCode, response.responseMessage)
        return response


class ClientProxy(Client):

    def call(self):
        # TODO.
        pass


mock_data = {
    'create-package': {
        'responseCode': 'OK',
        'responseMessage': '',
        'packageId': 1,
        'adminPersonId': 2,
        'supportPersonId': 3,
        'financePersonId': 4
    }
}

class ClientMock(Client):

    def mock_results(self, key):
        # This exists for easy mocking. TODO: think of a better way to do this.
        return mock_data[key]

    def call(self, client, name, data):
        """
        This fakes out the client and just looks up the values in mock_results
        for that service.
        """
        bango = Mock()
        for k, v in self.mock_results(name).iteritems():
            setattr(bango, k, v)
        self.is_error(bango)
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
