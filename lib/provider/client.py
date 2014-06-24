from collections import defaultdict

from django.conf import settings

from curling.lib import API
from solitude.logger import getLogger

log = getLogger('s.provider')
mock_data = defaultdict(dict)


class Client(object):

    def __init__(self, reference_name):
        self.config = settings.ZIPPY_CONFIGURATION.get(reference_name)
        self.api = None
        if self.config:
            self.api = API(self.config['url'], append_slash=False)
            self.api.activate_oauth(self.config['auth']['key'],
                                    self.config['auth']['secret'],
                                    params={'oauth_token': 'not-implemented'})
        else:
            log.warning('No config for {ref}; oauth disabled'
                        .format(ref=reference_name))


class APIMockObject(object):

    def __init__(self, resource_name, pk=None):
        self.mock_data = mock_data.copy()
        self.resource_name = resource_name
        self.pk = pk

    def __call__(self, pk):
        return self.__class__(self.resource_name, pk)

    def get(self):
        if self.pk:
            return self.get_data(self.resource_name)[self.pk]
        else:
            return (self.get_data(self.resource_name) and
                    self.get_data(self.resource_name).values() or [])

    def get_data(self, resource_name):
        """Exists to make mock patching easy."""
        return mock_data[resource_name]

    def post(self, data):
        id = data.get('pk', data.get('external_id'))
        data['uuid'] = 'ref:uuid'
        data['resource_pk'] = self.pk
        data['resource_name'] = self.resource_name
        data['resource_uri'] = '/{resource_name}/{resource_pk}'.format(
                               resource_pk=self.pk,
                               resource_name=self.resource_name)
        mock_data[self.resource_name][id] = data
        return self.get_data(self.resource_name)[id]


    def put(self, data):
        initial_data = mock_data[self.resource_name][self.pk]
        initial_data.update(data)
        mock_data[self.resource_name][self.pk] = initial_data
        return mock_data[self.resource_name][self.pk]

    def delete(self):
        del mock_data[self.resource_name][self.pk]


class APITransactionMockObject(APIMockObject):

    def post(self, data):
        transaction = super(APITransactionMockObject, self).post(data)
        transaction['status'] = 'STARTED'
        transaction['token'] = 'transaction-token'
        mock_data[self.resource_name][self.pk] = transaction
        return mock_data[self.resource_name][self.pk]


class APIMock(object):

    @property
    def sellers(self, *args, **kwargs):
        return APIMockObject('sellers')

    @property
    def products(self, *args, **kwargs):
        return APIMockObject('products')

    @property
    def transactions(self, *args, **kwargs):
        return APITransactionMockObject('transactions')


class ClientMock(object):

    def __init__(self, reference_name):
        self.api = APIMock()


class ClientProxy(object):

    def __init__(self, reference_name):
        proxy = settings.ZIPPY_PROXY
        if not settings.ZIPPY_PROXY.endswith('/'):
            proxy = proxy + '/'
        self.config = settings.ZIPPY_CONFIGURATION.get(reference_name)
        self.api = API(proxy + reference_name, append_slash=False)


def get_client(reference_name):
    """
    Use this to get the right client and communicate with Zippy.
    """
    if settings.ZIPPY_MOCK:
        return ClientMock(reference_name)
    if settings.ZIPPY_PROXY:
        return ClientProxy(reference_name)
    return Client(reference_name)
