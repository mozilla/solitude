import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client

from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
import test_utils


class APIClient(Client):

    def _process(self, kwargs):
        kwargs['content_type'] = 'application/json'
        if 'data' in kwargs:
            kwargs['data'] = json.dumps(kwargs['data'])
        return kwargs

    def post(self, *args, **kwargs):
        return super(APIClient, self).post(*args, **self._process(kwargs))


class APITest(test_utils.TestCase):
    client_class = APIClient

    def _pre_setup(self):
        super(APITest, self)._pre_setup()
        # For unknown reasons test_utils sets settings.DEBUG = True.
        # For more unknown reasons tastypie won't show you any error
        # tracebacks if settings.DEBUG = False.
        #
        # Let's set this to True so we've got a hope in hell of
        # debugging errors in the tests.
        settings.DEBUG = True

    def get_list_url(self, name):
        return reverse('api_dispatch_list', kwargs={'api_name': '1',
                                                    'resource_name': name})


    def get_detail_url(self, name, obj):
        return reverse('api_dispatch_detail', kwargs={'api_name': '1',
                                                      'resource_name': name,
                                                      'pk': obj.pk})

    def allowed_verbs(self, url, allowed):
        """
        Will run through all the verbs except the ones specified in allowed
        and ensure that hitting those produces a 405. Otherwise the test will
        fail.
        """
        verbs = ['get', 'post', 'put', 'delete']
        # TODO(andym): get patch in here.
        for verb in verbs:
            if verb in allowed:
                continue
            res = getattr(self.client, verb)(url)
            assert res.status_code in (401, 405), (
                   '%s: %s not 401 or 405' % (verb.upper(), res.status_code))

    def get_errors(self, content, field):
        return json.loads(content)[field]


class SolitudeAuthentication(Authentication):
    # TODO(andym): add in authentication here.
    pass


class SolitudeAuthorization(Authorization):
    pass


class SolitudeResource(ModelResource):

    class Meta:
        always_return_data = True
        authentication = SolitudeAuthentication()
        authorization = SolitudeAuthorization()
        serializer = Serializer(formats=['json'])
