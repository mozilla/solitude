import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client

from tastypie import http
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.resources import (ModelResource as TastyPieModelResource,
                                Resource as TastyPieResource)
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

    def put(self, *args, **kwargs):
        return super(APIClient, self).put(*args, **self._process(kwargs))


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

    def get_list_url(self, name, api_name=None):
        return reverse('api_dispatch_list',
                        kwargs={'api_name': api_name or self.api_name,
                                'resource_name': name})

    def get_detail_url(self, name, pk, api_name=None):
        pk = getattr(pk, 'pk', pk)
        return reverse('api_dispatch_detail',
                       kwargs={'api_name': api_name or self.api_name,
                               'resource_name': name, 'pk': pk})

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


class Authentication(Authentication):
    # TODO(andym): add in authentication here.
    pass


class Authorization(Authorization):
    pass


class BaseResource(object):

    def form_errors(self, forms):
        errors = {}
        if not isinstance(forms, list):
            forms = [forms]
        for f in forms:
            if isinstance(f.errors, list):  # Cope with formsets.
                for e in f.errors:
                    errors.update(e)
                continue
            errors.update(dict(f.errors.items()))

        response = http.HttpBadRequest(json.dumps(errors),
                                       content_type='application/json')
        return ImmediateHttpResponse(response=response)

    def get_object_or_404(self, cls, **filters):
        """
        A wrapper around our more familiar get_object_or_404, for when we need
        to get access to an object that isn't covered by get_obj.
        """
        if not filters:
            raise ImmediateHttpResponse(response=http.HttpNotFound())
        try:
            return cls.objects.get(**filters)
        except (cls.DoesNotExist, cls.MultipleObjectsReturned):
            raise ImmediateHttpResponse(response=http.HttpNotFound())


class Resource(BaseResource, TastyPieResource):

    class Meta:
        always_return_data = True
        authentication = Authentication()
        authorization = Authorization()
        serializer = Serializer(formats=['json'])


class ModelResource(BaseResource, TastyPieModelResource):

    class Meta:
        always_return_data = True
        authentication = Authentication()
        authorization = Authorization()
        serializer = Serializer(formats=['json'])
