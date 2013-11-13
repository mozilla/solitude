from django.conf import settings

from curling.lib import API

mock_data = {}


class Client(object):

    def __init__(self, reference_name):
        self.config = settings.ZIPPY_CONFIGURATION.get(reference_name)
        self.api = None
        if self.config:
            self.api = API(self.config['url'], append_slash=False)
            self.api.activate_oauth(self.config['auth']['key'],
                                    self.config['auth']['secret'])


class APIMockObject(object):

    def __init__(self, resource_name, uuid=None):
        self.resource_name = resource_name
        self.uuid = uuid
        self.last_pk = 0

    def __call__(self, uuid):
        return APIMockObject(self.resource_name, uuid)

    def get(self):
        if self.uuid:
            return mock_data[self.uuid]
        else:
            return mock_data and mock_data.values() or []

    def post(self, data):
        pk = self.last_pk + 1
        data['resource_pk'] = str(pk)
        data['resource_uri'] = '/{resource_name}/{pk}'.format(pk=pk,
                               resource_name=self.resource_name)
        self.last_pk += 1
        mock_data[data['uuid']] = data
        return mock_data[data['uuid']]

    def put(self, data):
        initial_data = mock_data[self.uuid]
        initial_data.update(data)
        mock_data[self.uuid] = initial_data
        return mock_data[self.uuid]

    def delete(self):
        del mock_data[self.uuid]


class APIMock(object):

    @property
    def sellers(self, *args, **kwargs):
        return APIMockObject('sellers')


class ClientMock(object):

    def __init__(self, reference_name):
        self.api = APIMock()


def get_client(reference_name):
    """
    Use this to get the right client and communicate with Zippy.
    """
    if settings.ZIPPY_MOCK:
        return ClientMock(reference_name)
    return Client(reference_name)
